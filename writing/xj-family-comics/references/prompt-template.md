# 生图提示词模板

每张图单独生成。按当前内容替换变量，**不要**把多格拼在一张里。固定角色块从 `characters.md` 原样粘贴，不要改写。

> **水印硬约束（每张都必须写）**：在 Visual DNA 开头与 Constraints 末尾都明确写「不要添加任何水印 / 签名 / logo / '图片由AI生成' 文字或角标」。

---

## A. 任务画像（封面全家福，每个任务先生成 1 张）

```text
Generate ONE standalone 4:3 horizontal hand-drawn comic "task portrait" (family cover illustration) for a parenting comic whose theme is: {本篇主题}.

IMPORTANT: Do NOT add any watermark, signature, logo, or "AI-generated" / "图片由AI生成" text or corner mark anywhere on the image.

Visual DNA:
Hand-drawn comic style (indie comic / watercolor-sketch picture-book feel). VISIBLE ink pen strokes, slightly wobbly sketchy hand-drawn lines, not vector-smooth, not clean clip-art. Soft pastel color fills on a warm paper-tone background with a subtle paper grain and gentle glow (no heavy noise, no grunge). Rounded cute-but-not-garish character design. Cozy family home atmosphere. Positive, warm, thoughtful mood. NOT anime battle, NOT realistic photo, NOT emoji-sticker, NOT dark or scary.

Recurring family IP characters (must stay consistent with the comic panels):
{=== 粘贴 characters.md 的「固定角色块」整段 ===}

Portrait scene:
The three family members together as a warm group, posed to hint at the theme "{本篇主题}" (e.g. a small symbolic prop or gesture, kept subtle—NOT a text title). 饺子 in the center brightest and cutest; 小鞋子 gentle on one side; 小修 scruffy-but-awake on the other. Soft warm glow, plenty of cozy empty paper space, no words/text on the image.

Composition notes:
Centered family group, medium-wide shot, gentle warm glow, minimal props, no speech bubbles, no title text. A calming cover image.

Color use:
Soft pastel palette on warm paper tone; warm colors for mood, calm blue/green for peaceful moments. Keep saturation low, brightness high, ink lines dark brown/near-black with visible stroke weight.

Constraints:
Keep characters' appearances IDENTICAL to the comic panels (same heads, same 3 buns for mom, same glasses + messy hair for dad, same clothing colors, same hand-drawn art style). 饺子 must look like a 1-year-old baby (huge head, big double-eyelid eyes, no speech). Warm, thoughtful, not preachy. NO watermark / signature / logo / "AI-generated" text or mark anywhere; clean warm paper background. If a generation returns with an AI watermark, remove it before delivering.
```

---

## B. 单格漫画（6 格，逐格生成）

```text
Generate ONE standalone 4:3 horizontal panel of a warm HAND-DRAWN parenting comic. This is panel {格号} of a 6-panel comic about: {本篇主题}.

IMPORTANT: Do NOT add any watermark, signature, logo, or "AI-generated" / "图片由AI生成" text or corner mark anywhere on the image.

Visual DNA:
Hand-drawn comic style (indie comic / watercolor-sketch picture-book feel). VISIBLE ink pen strokes, slightly wobbly sketchy hand-drawn lines, not vector-smooth, not clean clip-art. Soft pastel color fills on a warm paper-tone background with a subtle paper grain and gentle glow (no heavy noise, no grunge). Rounded cute-but-not-garish character design. Family home atmosphere with believable props. Positive, humorous yet thoughtful mood. NOT anime battle, NOT realistic photo, NOT emoji-sticker, NOT dark or scary.

Recurring family IP characters (must stay consistent across all panels):
{=== 粘贴 characters.md 的「固定角色块」整段 ===}

Panel scene (this panel only):
{该格画面：场景、发生了什么动作、谁在画面里、站位与占比}

Characters in this panel:
{本格登场的角色与各自动作}

Speech bubbles (Chinese, short, handwritten comic style, few words):
{气泡1：说话角色 + 内容} / {气泡2：说话角色 + 内容} / {饺子表情气泡：咿呀 / ？ / ！}

Composition notes:
{构图提示，参考 composition-patterns.md：如中景展示客厅、预留右上气泡空间、饺子视觉最亮最靠前}

Color use:
Soft pastel palette on warm paper tone; warm colors for mood, one accent warm color (orange/red) only for the emotional focus or a key prop; calm blue/green for peaceful or thinking moments. Keep saturation low, brightness high, ink lines dark brown/near-black with visible stroke weight.

Constraints:
One panel shows only one core action. Keep characters' appearances IDENTICAL to other panels (same heads, same 3 buns for mom, same glasses + messy hair for dad, same clothing colors, same hand-drawn art style). 饺子 must look like a 1-year-old baby (huge head, big double-eyelid eyes, no speech). Make it warm, gently funny, thoughtful—not preachy, not a crude meme, not saccharine. NO watermark / signature / logo / "AI-generated" text or mark anywhere; clean warm paper background. If a generation returns with an AI watermark, remove it before delivering.
```

---

## 图像编辑提示

去掉角落水印 / 标题：

```text
Edit the provided image. Remove only the small watermark / corner text "{要删除的文字}" from the bottom corner. Fill that area with the same warm paper-tone background, matching the surrounding panel. Preserve everything else exactly: characters, bubbles, line style, composition, aspect ratio, and image quality. Do not add any new text or objects.
```

增强一致性（某格角色跳变时重生成用）：

```text
Regenerate this panel with the SAME core meaning and layout, but strictly keep the family IP characters identical to the established hand-drawn design: 饺子 huge-head 1-year-old baby with big double-eyelid eyes and light onesie; 小鞋子 with exactly THREE small hair buns, gentle dress; 小修 with round glasses, messy hair, stubble, crooked collar, worn T-shirt. Same hand-drawn ink comic style with visible sketchy pen strokes, same clothing colors, same soft pastel-on-warm-paper palette. Warm comic, not cute-mascot, not realistic.
```
