# ComfyUI-SplitAssigner

An automated production task distribution and deadline scheduling node for ComfyUI.

Designed for creative leads, VFX coordinators, and design agencies, this node parses raw deliverable manifests (e.g., from Google Docs/Sheets extractors) and intelligently balances workloads across an artist team. It automatically calculates target deadlines based on daily slide throughput limits and studio calendar rules, while isolating video tasks into a dedicated department backlog.

---

## Features

- **Intelligent Workload Balancing:** Distributes graphic tasks across customizable artist pools using round-robin assignment weighted by slide/image count.
- **Calendar-Aware Deadline Engine:** Computes sequential completion dates based on configurable daily capacity, automatically skipping Sundays and alternating weekend off-days.
- **Department Routing:** Automatically detects video, reel, and UGC assets, routing them to a separate video department tracking summary without cluttering static design queues.
- **Name & Title Standardization:** Hardens messy incoming text against non-standard dashes, collapses whitespace anomalies, and replaces long product names with clean pipeline abbreviations.
- **Production-Ready Two-Line Output:** Formats each assigned task into a clean headline with calculated deadline on line 1, and the clickable asset brief URL on line 2 for direct sharing to Slack, ClickUp, or Notion.
- **Zero External Dependencies:** Built 100% on native Python standard libraries (`re`, `math`, `datetime`) with zero third-party packages required.

---

## Installation

1. Navigate to your ComfyUI custom nodes directory:
   cd ComfyUI/custom_nodes

2. Clone this repository:
   git clone https://github.com/harsh-shrivas/ComfyUI-SplitAssigner.git

3. Restart ComfyUI. (Zero external pip packages required).

---

## Usage

- **Category:** `Automation/Task Routing`
- **Node Name:** `Split Assigner Node`
- **Workflow:**
  1. Route extracted deliverable text (from `Google Workspace Extractor` or any text node) into `extracted_content`.
  2. Set `num_artists` to your active roster size (defaults to 2).
  3. Define `capacity_per_day` (defaults to 4 slides/day per designer).
  4. *(Optional)* Provide date bounds in `assigning_start_date`, `start_date`, or `end_date` using standard `DD/MM/YYYY` format.
  5. Click **Queue Prompt**. The node will output structured, copy-pasteable team schedules complete with individual delivery dates.

---

## Inputs & Outputs

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **extracted_content** | `STRING` (Input) | *Required* | Raw extracted text containing deliverable titles and links |
| **num_artists** | `INT` (Input) | `2` | Total number of graphic artists to distribute across |
| **capacity_per_day** | `INT` (Input) | `4` | Daily throughput threshold per artist in slides/units |
| **assigning_start_date** | `STRING` (Optional) | `""` | Baseline date (`DD/MM/YYYY`) to anchor deadline scheduling |
| **start_date** | `STRING` (Optional) | `""` | Earliest deliverable date filter cutoff |
| **end_date** | `STRING` (Optional) | `""` | Latest deliverable date filter cutoff |
| **all_schedules_formatted** | `STRING` (Output) | — | Department-split, itemized schedules with assigned deadlines |

---

## License

MIT License. Free to use, modify, and integrate into internal production environments and studio pipelines.
