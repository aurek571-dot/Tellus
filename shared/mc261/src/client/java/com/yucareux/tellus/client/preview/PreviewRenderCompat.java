package com.yucareux.tellus.client.preview;

import com.mojang.blaze3d.pipeline.RenderPipeline;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.state.gui.GuiElementRenderState;
import net.minecraft.resources.Identifier;

/**
 * Minecraft 26.1.2 variant: this release still uses the uniform/sampler based pipeline API
 * (no bind groups), so the preview reuses vanilla's GUI pipelines like the 1.21.11 build does.
 * Unlike the 26.2 build there is no dedicated depth-tested pipeline.
 */
public final class PreviewRenderCompat {
   private PreviewRenderCompat() {}

   public static void blitSun(GuiGraphicsExtractor graphics, Identifier texture, int x, int y, int size) {
      graphics.blit(RenderPipelines.GUI_TEXTURED, texture, x, y, 0.0F, 0.0F, size, size, 32, 32);
   }

   public abstract static class TerrainState implements GuiElementRenderState {
      @Override
      public RenderPipeline pipeline() {
         return RenderPipelines.GUI;
      }
   }
}
