import re
import math
from datetime import datetime, timedelta

# Flexible product abbreviation dictionary
PRODUCT_ABBREVIATIONS = {
    "acne solution": "ACS",
    "advanced reset": "ADR",
    "age arrest": "AAS",
    "barrier fortify": "BFM",
    "depigmentation": "DEP",
    "evergoing": "EVG",
    "hydrating": "HDR",
    "lucent reveal": "LRS",
    "mattifying gel": "MGM",
    "moisture boost": "MBC",
    "moisturizing": "MOI",
    "nourishing sleep": "NSC",
    "oil cleanse": "OLC",
    "pore minimizer": "PRM",
    "youth support": "YSC",
}

class SplitAssignerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "extracted_content": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "num_artists": ("INT", {"default": 2, "min": 1, "max": 10, "step": 1}),
                "capacity_per_day": ("INT", {"default": 4, "min": 1, "max": 20, "step": 1}),
                "assigning_start_date": ("STRING", {"default": "", "multiline": False, "placeholder": "dd/mm/yyyy"}),
                "start_date": ("STRING", {"default": "", "multiline": False, "placeholder": "dd/mm/yyyy"}),
                "end_date": ("STRING", {"default": "", "multiline": False, "placeholder": "dd/mm/yyyy"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("all_schedules_formatted",)
    FUNCTION = "assign_and_split_tasks"
    OUTPUT_NODE = True
    CATEGORY = "Automation/Task Routing"

    def _flexible_parse_date(self, date_input):
        if not date_input or not str(date_input).strip():
            return None

        clean_str = str(date_input).strip()
        
        if clean_str.lower() in ["dd/mm/yyyy", "dd.mm.yyyy", "dd-mm-yyyy"]:
            return None

        clean_str = clean_str.replace('/', '.').replace('-', '.')

        parts = clean_str.split('.')
        if len(parts) == 3:
            day, month, year = parts[0], parts[1], parts[2]
            if len(year) == 2:
                year = f"20{year}"
            clean_str = f"{day.zfill(2)}.{month.zfill(2)}.{year}"

        formats = ["%d.%m.%Y", "%Y.%m.%d", "%m.%d.%Y"]

        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue

        return None

    def _clean_whitespace_and_dashes(self, text):
        """ Hardens text against messy spaces, unicode dashes, and weird hyphen spacing """
        if not text:
            return ""

        # Replace non-standard dashes (em-dash, en-dash, figure dash) with standard hyphen
        text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)

        # Standardize space around hyphens inside bracket titles (e.g. "AAS- Post" -> "AAS - Post")
        text = re.sub(r'\s*-\s*', ' - ', text)

        # Fix spacing around brackets
        text = re.sub(r'\[\s+', '[', text)
        text = re.sub(r'\s+\]', ']', text)

        # Collapse multiple consecutive spaces into a single space
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()

    def _strip_existing_deadline(self, line):
        clean_line = re.sub(r'\s*:\s*\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}$', '', line).strip()
        return self._clean_whitespace_and_dashes(clean_line)

    def _apply_product_abbreviations(self, line):
        """ Replaces product names cleanly with word-boundary awareness """
        abbreviated_line = line
        for full_name_pattern, abbr in PRODUCT_ABBREVIATIONS.items():
            pattern = r'\b' + re.escape(full_name_pattern) + r'\b'
            abbreviated_line = re.sub(pattern, abbr, abbreviated_line, flags=re.IGNORECASE)
        
        return self._clean_whitespace_and_dashes(abbreviated_line)

    def _parse_task_date(self, line):
        clean_line = self._strip_existing_deadline(line)
        date_match = re.search(r'(\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4})', clean_line)
        if date_match:
            raw_date_str = date_match.group(1)
            parsed_dt = self._flexible_parse_date(raw_date_str)
            if parsed_dt:
                return parsed_dt, raw_date_str
        return None, None

    def _is_off_day(self, dt):
        weekday = dt.weekday()
        if weekday == 6:  # Sunday
            return True
        if weekday == 5:  # Saturday
            saturday_occurrence = math.ceil(dt.day / 7.0)
            if saturday_occurrence in (1, 3):
                return True
        return False

    def _calculate_deadline(self, start_dt, current_accumulated_slides, task_slides, capacity_per_day):
        total_slides_after_task = current_accumulated_slides + task_slides
        working_day_index = (total_slides_after_task - 1) // capacity_per_day

        curr_dt = start_dt
        while self._is_off_day(curr_dt):
            curr_dt += timedelta(days=1)

        work_days_count = 0
        while work_days_count < working_day_index:
            curr_dt += timedelta(days=1)
            if not self._is_off_day(curr_dt):
                work_days_count += 1

        return curr_dt

    def _format_task_clean_two_line(self, base_task_text, deadline_str=None):
        """ Formats titles cleanly while guaranteeing strict 2-line structure with raw URL on line 2 """
        link_match = re.search(r'\[(.*?)\]\((https?://[^\s)]+)\)', base_task_text)
        
        if link_match:
            raw_title = link_match.group(1)
            url_link = link_match.group(2)
            
            clean_title = self._clean_whitespace_and_dashes(raw_title)
            
            # Reconstruct title part preceding bracket if present (e.g. "09/11/2026 - ")
            prefix_match = re.match(r'^(.*?)\s*\[', base_task_text)
            prefix = self._clean_whitespace_and_dashes(prefix_match.group(1)) if prefix_match else ""
            
            if prefix:
                clean_line_head = f"{prefix} [{clean_title}]"
            else:
                clean_line_head = f"[{clean_title}]"
            
            clean_line_head = self._clean_whitespace_and_dashes(clean_line_head)
            
            if deadline_str:
                return f"{clean_line_head} : {deadline_str}\n({url_link})"
            else:
                return f"{clean_line_head}\n({url_link})"
        else:
            clean_base = self._clean_whitespace_and_dashes(base_task_text)
            if deadline_str:
                return f"{clean_base} : {deadline_str}"
            else:
                return f"{clean_base}"

    def assign_and_split_tasks(self, extracted_content, num_artists=2, capacity_per_day=4, assigning_start_date="", start_date="", end_date=""):
        if not extracted_content or not extracted_content.strip():
            return ("No extracted tasks found.",)

        global_assign_start_dt = self._flexible_parse_date(assigning_start_date)
        start_limit_dt = self._flexible_parse_date(start_date)
        end_limit_dt = self._flexible_parse_date(end_date)

        raw_lines = [line.strip() for line in extracted_content.strip().split("\n") if line.strip()]

        filtered_tasks = []
        for line in raw_lines:
            if line.startswith("=") or line.startswith("📊") or line.startswith("•"):
                continue

            task_dt, _ = self._parse_task_date(line)
            if task_dt:
                if start_limit_dt and task_dt < start_limit_dt:
                    continue
                if end_limit_dt and task_dt > end_limit_dt:
                    continue

            shortened_line = self._apply_product_abbreviations(line)
            filtered_tasks.append(shortened_line)

        if not filtered_tasks:
            return ("No tasks matched the selected filter criteria.",)

        artist_buckets = [[] for _ in range(num_artists)]
        artist_image_counts = [0] * num_artists
        video_dept_tasks = []

        rr_counter = 0

        for line in filtered_tasks:
            base_task_text = self._strip_existing_deadline(line)
            line_lower = base_task_text.lower()

            slide_match = re.search(r'x(\d+)', base_task_text, re.IGNORECASE)
            image_count = int(slide_match.group(1)) if slide_match else 1

            task_dt, _ = self._parse_task_date(base_task_text)
            base_dt = global_assign_start_dt if global_assign_start_dt else (task_dt or start_limit_dt or datetime.now())

            # 1. VIDEO DEPT (SUMMARY ONLY, NO DEADLINES)
            if any(k in line_lower for k in ["ugc", "reel", "video"]):
                formatted_entry = self._format_task_clean_two_line(base_task_text, deadline_str=None)
                video_dept_tasks.append(formatted_entry)

            # 2. BREAKS TO ARTIST 1
            elif "break" in line_lower:
                assigned_artist_idx = 0
                current_artist_slides = artist_image_counts[assigned_artist_idx]
                deadline_dt = self._calculate_deadline(base_dt, current_artist_slides, image_count, capacity_per_day)
                deadline_str = deadline_dt.strftime("%d/%m/%Y")

                formatted_entry = self._format_task_clean_two_line(base_task_text, deadline_str=deadline_str)

                artist_buckets[assigned_artist_idx].append(formatted_entry)
                artist_image_counts[assigned_artist_idx] += image_count

            # 3. GRAPHIC DESIGNERS
            else:
                assigned_artist_idx = rr_counter % num_artists
                rr_counter += 1

                current_artist_slides = artist_image_counts[assigned_artist_idx]
                deadline_dt = self._calculate_deadline(base_dt, current_artist_slides, image_count, capacity_per_day)
                deadline_str = deadline_dt.strftime("%d/%m/%Y")

                formatted_entry = self._format_task_clean_two_line(base_task_text, deadline_str=deadline_str)

                artist_buckets[assigned_artist_idx].append(formatted_entry)
                artist_image_counts[assigned_artist_idx] += image_count

        formatted_sections = []
        assign_start_disp = global_assign_start_dt.strftime("%d/%m/%Y") if global_assign_start_dt else "Creative Upload Dates"
        start_disp = start_limit_dt.strftime("%d/%m/%Y") if start_limit_dt else "All Start"
        end_disp = end_limit_dt.strftime("%d/%m/%Y") if end_limit_dt else "All End"

        date_range_info = f"📅 Active Range: {start_disp} to {end_disp} | Start: {assign_start_disp} | Capacity: {capacity_per_day} slides/day"

        # 1. Video Section
        video_header = (
            f"==================================================\n"
            f"🎥 VIDEO DEPARTMENT (UNASSIGNED SUMMARY)\n"
            f"📊 Total Video Deliverables: {len(video_dept_tasks)}\n"
            f"=================================================="
        )
        video_lines = [f"{v_idx:02d}. {v_task}" for v_idx, v_task in enumerate(video_dept_tasks, 1)]
        video_section = f"{video_header}\n" + ("\n\n".join(video_lines) if video_lines else "No video/UGC/reel tasks found.")
        formatted_sections.append(video_section)

        # 2. Artist Schedules
        for idx, tasks in enumerate(artist_buckets):
            artist_name = f"Artist {idx + 1:02d}"
            total_tasks = len(tasks)
            total_images = artist_image_counts[idx]

            header = (
                f"==================================================\n"
                f"🎨 WORK SCHEDULE: {artist_name.upper()}\n"
                f"📊 {date_range_info}\n"
                f"📊 Total Tasks: {total_tasks} | Total Images/Slides: {total_images}\n"
                f"=================================================="
            )

            task_lines = [f"{t_idx:02d}. {task}" for t_idx, task in enumerate(tasks, 1)]
            section_text = f"{header}\n" + ("\n\n".join(task_lines) if task_lines else "No tasks assigned in this range.")

            formatted_sections.append(section_text)

        combined_schedules = "\n\n".join(formatted_sections)
        return (combined_schedules,)


NODE_CLASS_MAPPINGS = {"SplitAssigner": SplitAssignerNode}
NODE_DISPLAY_NAME_MAPPINGS = {"SplitAssigner": "Split Assigner Node"}
