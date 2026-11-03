package com.yucareux.tellus.mixin.client;

import com.yucareux.tellus.client.LoadingTerrainScreenTiming;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Minecraft 26.1.2 keeps the current screen on Minecraft itself (26.2 moved it to Gui). */
@Mixin({Minecraft.class})
public abstract class MinecraftScreenMixin {
   @Shadow
   public Screen screen;

   @Inject(
      method = {"setScreen"},
      at = {@At("HEAD")}
   )
   private void tellus$trackLoadingTerrainScreen(Screen newScreen, CallbackInfo ci) {
      LoadingTerrainScreenTiming.onScreenChange(this.screen, newScreen);
   }
}
