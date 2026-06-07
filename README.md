# 🎹 Music Workshop — AI 辅助作曲桌面软件

> **用键盘作曲，用波形造音，用 AI 写歌。**
> 一个从零合成乐器波形、用电脑键盘弹琴作曲、可视化五线谱的桌面音乐创作工具。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python">
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52" alt="PySide6">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Status-1.0-brightgreen" alt="Status">
</p>

---

## ✨ 核心功能

### 🎸 专业乐器模拟（纯波形合成）

不依赖任何采样库，通过数学算法直接生成声波来模拟真实乐器音色：

| 合成方法 | 原理 | 适用乐器 | 真实度 |
|----------|------|----------|--------|
| **Karplus-Strong** | 延迟线 + 低通反馈，模拟拨弦物理 | 钢琴、吉他、竖琴 | 60-70% |
| **FM 合成** | 频率调制产生丰富泛音 | 电钢、铜管、贝斯 | 60-75% |
| **加法合成** | 叠加多个谐波正弦波 | 管风琴、弦乐 | 70-80% |
| **模态合成** | 多个谐振模式 + 激励噪声 | 马林巴、钟琴 | 70-85% |

> 合成音色对作曲编曲完全足够。后续可通过多层 KS + 混合采样进一步提升。

### ⌨️ 键盘作曲

用电脑键盘像弹钢琴一样输入旋律。**经典双行布局**（大多数虚拟钢琴的标准）：

```
中间行（白键）：A→C4  S→D4  D→E4  F→F4  G→G4  H→A4  J→B4  K→C5  L→D5  ;→E5
上  行（黑键）：W→C#4  E→D#4  T→F#4  Y→G#4  U→A#4  O→C#5  P→D#5
下  行（低音）：Z→B3   X→C4   C→D4   V→E4   B→F4   N→G4   M→A4  ,→B4  .→C5  /→D5
```

- **左手放 ZXCVBNM**（低音区），**右手放 ASDFGHJKL**（主音区）
- **升降八度**：`Shift+Z`（降）/ `Shift+X`（升）
- **力度控制**：`Ctrl` = 弱 (60)，`Alt` = 中 (80)，默认 = 强 (100)
- **量化精度可调**：全音符到 32 分音符

### 🎼 五线谱实时渲染

录音后自动生成标准五线谱（VexFlow 引擎）：

- 实时音符显示（录一个音刷新一次）
- 多种量化精度适配
- MIDI / MusicXML / LilyPond 导出

### 🤖 AI 辅助作曲

支持 [DeepSeek API](https://platform.deepseek.com/)（OpenAI 兼容），提供：

- **旋律续写** — 给出开头，AI 补完
- **和弦推荐** — 根据旋律推荐和弦进行
- 不设 API Key 自动降级为本地算法（完全离线）

---

## 🧱 技术栈

| 层 | 技术 | 选型理由 |
|---|------|---------|
| **语言** | Python 3.11+ | 生态丰富、开发快 |
| **GUI** | PySide6 (Qt6) | 原生桌面、QPainter 绘图、QWebEngineView |
| **音频引擎** | numpy + sounddevice | 实时音频、低延迟、纯 Python DSP |
| **合成器** | 自实现 (numpy) | 完全掌控波形生成逻辑 |
| **乐谱渲染** | music21 + VexFlow | 专业乐谱数据模型 + 浏览器级渲染 |
| **AI** | OpenAI SDK → DeepSeek API | OpenAI 兼容协议，低成本高效果 |

---

## 📁 项目结构

```
music_workshop/
├── main.py                         # 程序入口
├── pyproject.toml                  # 依赖配置
├── .env                            # API 密钥（已配置）
├── .gitignore
│
├── music_workshop/
│   ├── app.py                      # 应用配置（加载 .env）
│   │
│   ├── audio/                      # 音频引擎（纯 numpy，零 Qt 依赖）
│   │   ├── engine.py               # AudioEngine — sounddevice 实时音频流
│   │   ├── mixer.py                # Mixer — 32声部池 + 效果链
│   │   ├── voice.py                # Voice — 合成器+包络封装
│   │   ├── envelope.py             # ADSREnvelope — 四段包络
│   │   └── synths/
│   │       ├── base.py             # BaseSynthesizer (ABC)
│   │       ├── karplus_strong.py   # Karplus-Strong 物理建模
│   │       ├── fm.py               # FM 合成（DX7 算子路由）
│   │       ├── additive.py         # 加法合成（谐波叠加）
│   │       └── modal.py            # 模态合成（打击乐）
│   │
│   ├── audio/effects/
│   │   ├── base.py                 # 效果器基类 + CombFilter / AllPassFilter
│   │   ├── reverb.py               # SchroederReverb 混响
│   │   └── chorus.py               # ChorusEffect 合唱
│   │
│   ├── instruments/
│   │   ├── registry.py             # 乐器注册表/工厂
│   │   └── presets.py              # 10 种内置乐器预设
│   │
│   ├── input/
│   │   ├── keyboard_mapper.py      # QWERTY 键盘 → MIDI 音符
│   │   ├── quantizer.py            # 音符时值量化器
│   │   └── recorder.py             # 录音器（按键→乐谱）
│   │
│   ├── score/
│   │   ├── score_manager.py        # music21 乐谱管理器（多轨+撤销）
│   │   ├── export.py               # VexFlow JSON 导出
│   │   ├── importer.py             # MIDI 文件导入
│   │   ├── undo_manager.py         # 撤销/重做引擎
│   │   └── project.py              # 项目文件保存/加载 (.mwproj)
│   │
│   ├── ai/                         # AI 辅助作曲
│   │   ├── client.py               # DeepSeek API 客户端
│   │   ├── melody.py               # 旋律续写助手
│   │   └── harmony.py              # 和弦推荐助手
│   │
│   ├── ui/
│   │   ├── main_window.py          # 主窗口（布局管理）
│   │   ├── piano_widget.py         # 钢琴键盘可视化控件
│   │   ├── notation_view.py        # 五线谱显示 (QWebEngineView)
│   │   ├── instrument_panel.py     # 乐器选择面板
│   │   ├── transport_bar.py        # 传输控制栏（录音/导出/撤销）
│   │   └── ai_panel.py             # AI 建议面板
│   │
│   └── resources/
│       └── vexflow_renderer.html   # VexFlow 五线谱渲染页面
│
└── tests/
```

---

## 🚀 快速开始

### 前置条件

- Python 3.11+
- 声卡（任何电脑都有）

### 安装与运行

```bash
# 克隆项目
git clone https://github.com/yourname/music-workshop.git
cd music-workshop

# 创建虚拟环境（隔离系统包）
python -m venv .venv

# 安装依赖
.venv/Scripts/pip install PySide6 numpy sounddevice music21 openai python-dotenv

# 运行！
.venv/Scripts/python main.py
```

### 使用指南

```text
1. 按 Record 按钮开始录音
2. 用键盘弹旋律（Z/X/C/V = C/D/E/F...）
3. 再按 Record 停止
4. 五线谱自动生成！
5. 在 Instrument 面板切换乐器音色
6. 调整 BPM 和量化精度控制谱面
7. 按 Save 保存项目 (.mwproj)
8. 按 MIDI 导出标准 MIDI 文件
9. AI Composer 面板 → 旋律续写 / 和弦推荐
```

### AI 功能配置

项目已包含 `.env` 文件，AI 功能开箱即用：

```bash
# .env 文件内容
DEEPSEEK_API_KEY=sk-f7292********************
```

> ⚠️ **安全提醒**：`.env` 已在 `.gitignore` 中，不会被提交到 Git 仓库。
> 如果不配置 API Key，AI 面板会自动使用本地算法（不发送网络请求）。

---

## 🗺 开发路线图

| 阶段 | 里程碑 | 状态 |
|------|--------|------|
| **Phase 1** | 能发声 — KS 合成器 + 键盘映射 + 钢琴控件 | ✅ |
| **Phase 2** | 能看谱 — 录音 + 量化 + 五线谱渲染 | ✅ |
| **Phase 3** | 乐团 — FM/加法/模态合成 + 10乐器 + 效果器 | ✅ |
| **Phase 4** | 作曲工作台 — MIDI 导入导出、多轨、撤销重做、项目保存 | ✅ |
| **Phase 5** | AI 作曲家 — DeepSeek API 旋律续写、和弦推荐 | ✅ |

---

## ⚙️ 波形合成原理（核心）

每种乐器由**三个层面**定义：

```
乐器音色 = 合成算法(参数) × ADSR包络 + 效果链
```

以钢琴为例（Karplus-Strong 算法）：

```text
初始化延迟线：buffer = random[-0.5, 0.5] × 168 个采样 (C4)
每个采样点：
  output = buffer[idx]                    ← 输出当前值
  avg = 0.7×buffer[idx] + 0.3×buffer[idx+1]  ← 低通滤波
  buffer[idx] = avg × 0.998              ← 衰减回写
  idx = (idx + 1) % 168                  ← 循环递进
```

合成波形与真实钢琴波形对比：

| 方面 | 合成（KS） | 真实钢琴 | 差距 |
|------|-----------|---------|------|
| 起音瞬态 | 随机噪声→滤波 | 音槌击弦复杂瞬态 | ⚠️ 有差距 |
| 泛音结构 | 平滑指数衰减 | 精细谐波峰谷 | ⚠️ 可感知 |
| 音高/衰减 | 准确 | 准确 | ✅ 一致 |
| 和弦/多音 | 独立声部 | 独立琴弦 | ✅ 一致 |

---

## 🔧 架构设计

### 线程模型

```
┌─────────────────────────────────────────────────────┐
│  UI 线程（Qt 主循环）                                 │
│  - 界面绘制、键盘事件、Signal/Slot                    │
│  - 永不阻塞 >5ms                                     │
└──────────────────┬──────────────────────────────────┘
                   │ Queue（线程安全）
                   ▼
┌─────────────────────────────────────────────────────┐
│  音频回调线程（PortAudio 实时线程）                    │
│  - 每 ~5.3ms 调用一次                                │
│  - 不分配内存、不持锁、不 I/O                          │
│  - 从 Queue 接收事件 → 混合音频 → 写入声卡缓冲区        │
└─────────────────────────────────────────────────────┘
```

### 数据流

```text
键盘输入 → PianoWidget ──→ AudioEngine（发声）
                        └─→ Recorder（录音）
                              ↓
                          Quantizer（量化）
                              ↓
                        ScoreManager（乐谱）
                              ↓
                        VexFlow JSON → NotationView（显示）
```

---

## 🤝 贡献

欢迎任何形式的贡献！请提交 Issue 或 Pull Request。

---

## 📄 许可

[MIT License](LICENSE)

---

## 🙏 致谢

- [VexFlow](https://vexflow.com/) — 专业的五线谱 JavaScript 渲染库
- [music21](https://web.mit.edu/music21/) — MIT 开发的音乐分析工具包
- [sounddevice](https://python-sounddevice.readthedocs.io/) — PortAudio 的 Python 绑定
- [DeepSeek](https://deepseek.com/) — 高性价比 AI API
- 以及 **Yamaha DX7** — FM 合成的黄金标准

---

> **Music Workshop** — 让每个人都能用键盘创作音乐 🎵
