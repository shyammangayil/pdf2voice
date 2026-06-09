from core.models import Book, AudioSegment, Timeline, TimelineClip, Chunk

class TimelineBuilder:
    def build(self, book: Book, chunks: list[Chunk], audio_segments: list[AudioSegment]) -> Timeline:
        timeline = Timeline()
        
        # Map chunk_id to its audio segment
        audio_map = {seg.chunk_id: seg for seg in audio_segments}
        current_time = 0.0

        for chunk in chunks:
            seg = audio_map.get(chunk.chunk_id)
            if not seg:
                continue
                
            target_pages = chunk.target_pages
            num_pages = len(target_pages)
            
            # Calculate word count per page in this chunk to split audio proportionally
            page_words = {}
            total_chunk_words = 0
            
            for ch in book.chapters:
                for page in ch.pages:
                    if page.page_number in target_pages:
                        words = page.word_count
                        page_words[page.page_number] = max(1, words) # Prevent division by zero
                        total_chunk_words += page_words[page.page_number]
            
            time_offset = 0.0
            for page_num in target_pages:
                words = page_words.get(page_num, 1)
                ratio = words / total_chunk_words
                duration = seg.duration * ratio
                
                # Find the image path for this page
                img_path = ""
                for ch in book.chapters:
                    for p in ch.pages:
                        if p.page_number == page_num:
                            img_path = p.image_path
                            break
                
                clip = TimelineClip(
                    page_number=page_num,
                    image_path=img_path,
                    start_time=current_time,
                    end_time=current_time + duration,
                    audio_path=seg.file_path,          # Link the actual audio file
                    audio_start_offset=time_offset     # Tell FFmpeg where to start in this file
                )
                timeline.clips.append(clip)
                current_time += duration
                time_offset += duration

        return timeline