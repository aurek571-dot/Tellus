#!/usr/bin/env python3
"""Static mixin sanity check against a Minecraft jar classpath (uses javap).

Usage: check_mixins.py <classpath> <source-root>...   (later roots override earlier ones by relative path)
Reports @Mixin targets, @Shadow members, injector `method=` names, @Accessor fields and
@Redirect `target=` owners that do not exist in the given Minecraft classes.
"""
import os, re, subprocess, sys

cp = sys.argv[1]
roots = sys.argv[2:]
files = {}
for root in roots:
    for dp, _, fn in os.walk(root):
        if '/mixin/' not in dp.replace('\\', '/') + '/':
            continue
        for f in fn:
            if f.endswith('.java'):
                files[os.path.relpath(os.path.join(dp, f), root)] = os.path.join(dp, f)

cache = {}
def members(fqn):
    if fqn in cache:
        return cache[fqn]
    r = subprocess.run(['javap', '-p', '-cp', cp, fqn], capture_output=True, text=True)
    if r.returncode != 0:
        cache[fqn] = None
        return None
    names = set()
    for line in r.stdout.splitlines():
        m = re.search(r'(\w+|<init>)\s*\(', line)
        if m and ';' in line:
            names.add(m.group(1))
        m2 = re.search(r'(\w+);\s*$', line)
        if m2 and '(' not in line:
            names.add(m2.group(1))
    cache[fqn] = names
    return names

def resolve(simple, imports, pkg):
    simple = simple.replace('.', '$') if simple[0].islower() else simple
    if simple in imports:
        return imports[simple]
    head = simple.split('$')[0]
    if head in imports:
        return imports[head] + simple[len(head):].replace('.', '$')
    return pkg + '.' + simple

bad = 0
checked = 0
for rel, path in sorted(files.items()):
    src = open(path, encoding='utf-8').read()
    pkg = (re.search(r'^package\s+([\w.]+);', src, re.M) or [None, ''])[1]
    imports = {}
    for m in re.finditer(r'^import\s+(?:static\s+)?([\w.]+)\.(\w+);', src, re.M):
        imports[m.group(2)] = m.group(1) + '.' + m.group(2)
    # nested imports like LevelLoadingScreen.Reason resolve through the outer class below
    mx = re.search(r'@Mixin\s*\(([^)]*)\)', src)
    if not mx:
        continue
    body = mx.group(1)
    targets = []
    for m in re.finditer(r'([\w.]+)\.class', body):
        targets.append(resolve(m.group(1), imports, pkg))
    for m in re.finditer(r'"([\w.$/]+)"', body):
        targets.append(m.group(1).replace('/', '.'))
    print(f'--- {rel}: targets={targets}')
    mems = [members(t) for t in targets]
    if not targets or all(m is None for m in mems):
        print(f'    NOTE: target class not in Minecraft jars (external mod / missing): {targets}')
        continue
    for t, m in zip(targets, mems):
        if m is None:
            print(f'    FAIL: target class not found: {t}'); bad += 1
    allm = set().union(*[m for m in mems if m])
    # @Shadow members
    for m in re.finditer(r'@Shadow[^\n]*\n(?:\s*@\w+[^\n]*\n)*\s*(?:(?:public|private|protected|static|final|abstract)\s+)*[\w<>\[\],.? ]+?\s+(\w+)\s*(?:[;(=])', src):
        name = m.group(1); checked += 1
        if name not in allm:
            print(f'    FAIL: @Shadow {name} not found in target'); bad += 1
    # injector method names
    for m in re.finditer(r'method\s*=\s*(\{[^}]*\}|"[^"]*")', src):
        for n in re.findall(r'"([^"]+)"', m.group(1)):
            name = n.split('(')[0]; checked += 1
            if name in ('<init>', '<clinit>'):
                continue
            if name not in allm:
                print(f'    FAIL: injector method {n} not found in target'); bad += 1
    # accessors / invokers
    for m in re.finditer(r'@(?:Accessor|Invoker)\s*\(\s*"(\w+)"\s*\)', src):
        checked += 1
        if m.group(1) not in allm:
            print(f'    FAIL: @Accessor/@Invoker {m.group(1)} not found'); bad += 1
    # redirect/wrap target owners
    for m in re.finditer(r'target\s*=\s*"L([\w/$]+);(\w+)', src):
        owner = m.group(1).replace('/', '.'); name = m.group(2); checked += 1
        om = members(owner)
        if om is None:
            if not owner.startswith('java.'):
                print(f'    FAIL: @At target owner class not found: {owner}'); bad += 1
        elif name not in om:
            print(f'    FAIL: @At target {owner}.{name} not found'); bad += 1
print(f'\nCHECKED {checked} references across {len(files)} mixin files; FAILURES: {bad}')
