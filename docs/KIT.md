# KIT · 写段规范（学 lyric-mv docs/v4/KIT.md 的结构）

> 与 PLAN §7 目录清单一致；写任何段落前先读本文件与 docs/STORYBOARD.md。

## 1. 段落文件形状

`src/scenes/sec_NN_name.py` 导出 `shots(env) -> list[shot]`，每个 shot：

```python
{ "id", "at",            # 切点：B(小节)/Bt(拍)/H(词行)/T(词行精确) —— 禁止裸秒数
  "lines",               # [first,last] 该镜负责的歌词行
  "moment",              # 一句话：这是对话/宇宙的哪一个时刻
  "layout",              # boot/shell/grid2d/grid3d/cardstack/desk/plate/code/raw/crt
  "palette",             # 状态名或 (t)->spec
  "enter",               # 转场 spec：reflow/zoom/pan/spin/crt/winpop/fade/cut
  "camera",              # (t)->(x,y,zoom,rot)，对象匹配机位
  "render", }            # (ctx,t)->None，纯函数
```

时间函数（src/cues.py）：`B(bar)` `Bt(beat)`（可小数，133.5=反拍）`T(i)`（词行 i 精确起点）
`H(i)`（词行 i 吸附半拍）`P`（一拍秒数）`cue(name)`（非网格时间，只改 cues.py）。

## 2. 组件清单

| 组件 | 用法 |
|---|---|
| `components/terminal.py` | BIOS 日志、`>>>` 提示符、键入行+游标、进度条、hexdump |
| `components/code.py` | 多语言代码清单、行号、当前行高亮、错误标签（语法高亮色） |
| `components/formula.py` | 真公式规范排版（衬线斜体）；代数心形隐式曲线求根逐点描出 |
| `components/hud.py` | 常驻框架：CRT 底/频谱细带/字幕带/日志窗框（不计入 8 层底线） |
| `components/subtitle.py` | 英文逐词点亮（≤0.25s+flicker+青/金着色）+中文第二行 |
| `components/fractal.py` | 曼德博/朱利亚（numpy 分块、降采样放大） |
| `components/dialogs.py` | 警告弹窗、嵌套窗口、winpop/winclose |
| `components/spectrum.py` | 底部细频谱带（data/audio_features.json 驱动） |
| `components/char.py` | 界面立绘窗（8 套表情）；数据形态生成器：点阵侧脸/本轮轮廓/
  ASCII 字符鲸鱼/波函数云/星图核心/双螺旋——数据形态禁止引用 assets/char 立绘。
  「脸叠亮底」唯一标准处理=暗底椭圆法（脸区压暗至 ≤45% + 白点在上）；audit 脸部指标
  一律按区域限定（例如 S14 限定心形包围盒内），防止全帧白字污染统计 |

转场（engine/transitions.py）：reflow（Hilbert 粒子）、zoom（对象匹配）、pan（空间邻居）、
spin、crt（仅开关机）、winpop、fade、冲击位移（≤6 帧锁拍）。每个有理由注释。
engine/post.py：扫描线/暗角/余辉/受控色散（只按剧情开关）。

## 3. 图层与驱动表写法

每段分镜给出「命名层清单（≥8，其中 ≥6 本段专用动态层，角色层计动态）+ 运动驱动表」：
每层一行：层名 → 驱动源（词 onset / 拍点 / 低频能量 / 高频 onset / 进程状态 /
单向时间演化）。实现时层=独立绘制函数，禁止互相改状态。

## 4. 质量门槛

- 每帧 ≥8 层、≥6 动态；稳定内容密度 ≥ dsh TUI 参考；可溯源运动像素 ≥95%；
  无驱动抖动 <1%；9 宫格动态覆盖 ≥70%（tools/audit.py）。
- 转场有理由注释；相邻段布局不重复（EXECUTION 十二轮除外）。
- 闪光预算：任意 1 秒亮度往返 ≤3（tools/check_flash.py）；花屏图案 ≥6 帧。
- 光棘轮：镜头内只升不降，降只在切点（tools/luma.py）。

## 5. 检查方法

```text
.venv\Scripts\python film.py --stills 16.04,30.5,192.3          # 静帧卡片
.venv\Scripts\python tools\audit.py                             # 密度/层/抖动
.venv\Scripts\python tools\check_flash.py out\chk.mp4           # 闪光
.venv\Scripts\python tools\luma.py out\chk.mp4 --cuts ...        # 光棘轮
.venv\Scripts\python tools\verify.py                            # 字节一致
```

改共用组件前后跑回归比对（tools/sheets.py + tools/compare.py），非目标差异必须为 0。
