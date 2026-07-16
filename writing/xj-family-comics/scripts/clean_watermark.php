<?php
// 去除「图片由 AI 生成」类底部角落水印：将底部条带与底部两角填充为背景纸色。
//
// 用法（在 skill 根目录下）：
//   php scripts/clean_watermark.php                 # 仅处理 assets/family-ip 校准图
//   php scripts/clean_watermark.php 路径/某篇目录    # 处理该目录下所有 *.png
//   php scripts/clean_watermark.php a.png b.png      # 处理指定文件
//
// 模型无法看图、本机无 Python；用 PHP GD 做程序化底部填充，不碰中央角色与台词。

function avgCornerColor($im, $x0, $y0, $x1, $y1) {
    $r = $g = $b = 0; $n = 0;
    for ($y = $y0; $y <= $y1; $y++) {
        for ($x = $x0; $x <= $x1; $x++) {
            $c = imagecolorat($im, $x, $y);
            $r += ($c >> 16) & 0xFF;
            $g += ($c >> 8) & 0xFF;
            $b += $c & 0xFF;
            $n++;
        }
    }
    return [intval($r/$n), intval($g/$n), intval($b/$n)];
}

function cleanOne($path) {
    if (!file_exists($path)) { echo "skip (not found): $path\n"; return; }
    $im = imagecreatefrompng($path);
    if (!$im) { echo "fail load: $path\n"; return; }
    $w = imagesx($im); $h = imagesy($im);

    $tl = avgCornerColor($im, 0, 0, 9, 9);
    $tr = avgCornerColor($im, $w-10, 0, $w-1, 9);
    $bl = avgCornerColor($im, 0, $h-10, 9, $h-1);
    $br = avgCornerColor($im, $w-10, $h-10, $w-1, $h-1);
    $bc = avgCornerColor($im, intval($w/2)-5, $h-10, intval($w/2)+4, $h-1);
    $bg = [
        intval(($tl[0]+$tr[0]+$bl[0]+$br[0]+$bc[0])/5),
        intval(($tl[1]+$tr[1]+$bl[1]+$br[1]+$bc[1])/5),
        intval(($tl[2]+$tr[2]+$bl[2]+$br[2]+$bc[2])/5),
    ];
    $fill = imagecolorallocate($im, $bg[0], $bg[1], $bg[2]);

    $strip = 56;
    imagefilledrectangle($im, 0, $h - $strip, $w - 1, $h - 1, $fill);
    $cw = 320; $ch = 90;
    imagefilledrectangle($im, 0, $h - $ch, min($cw, $w-1), $h - 1, $fill);
    imagefilledrectangle($im, max(0, $w - $cw), $h - $ch, $w - 1, $h - 1, $fill);

    imagepng($im, $path);
    imagedestroy($im);
    echo "cleaned: $path (bg rgb={$bg[0]},{$bg[1]},{$bg[2]})\n";
}

$root = dirname(__DIR__);
$args = array_slice($argv, 1);

if (empty($args)) {
    // 默认：仅处理校准图
    $dir = $root . '/assets/family-ip';
    foreach (glob($dir . '/*.png') as $p) cleanOne($p);
} else {
    foreach ($args as $a) {
        if (is_dir($a)) {
            foreach (glob(rtrim($a, '/') . '/*.png') as $p) cleanOne($p);
        } else {
            cleanOne($a);
        }
    }
}
echo "done\n";
