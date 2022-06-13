from pydub import AudioSegment
import itertools

class Chunk:
    def db_to_float(self, db, using_amplitude=True):
        db = float(db)
        if using_amplitude:
            return 10 ** (db / 20)
        else:  # using power
            return 10 ** (db / 10)


    def detect_silence(self, audio_segment, min_silence_len=1000, silence_thresh=-16, seek_step=1):
        """
        Returns a list of all silent sections [start, end] in milliseconds of audio_segment.
        Inverse of detect_nonsilent()

        audio_segment - the segment to find silence in
        min_silence_len - the minimum length for any silent section
        silence_thresh - the upper bound for how quiet is silent in dFBS
        seek_step - step size for interating over the segment in ms
        """
        seg_len = len(audio_segment)

        # you can't have a silent portion of a sound that is longer than the sound
        if seg_len < min_silence_len:
            return []

        # convert silence threshold to a float value (so we can compare it to rms)
        silence_thresh = self.db_to_float(silence_thresh) * audio_segment.max_possible_amplitude

        # find silence and add start and end indicies to the to_cut list
        silence_starts = []

        # check successive (1 sec by default) chunk of sound for silence
        # try a chunk at every "seek step" (or every chunk for a seek step == 1)
        last_slice_start = seg_len - min_silence_len
        slice_starts = range(0, last_slice_start + 1, seek_step)

        # guarantee last_slice_start is included in the range
        # to make sure the last portion of the audio is searched
        if last_slice_start % seek_step:
            slice_starts = itertools.chain(slice_starts, [last_slice_start])

        for i in slice_starts:
            audio_slice = audio_segment[i:i + min_silence_len]
            if audio_slice.rms <= silence_thresh:
                silence_starts.append(i)

        # short circuit when there is no silence
        if not silence_starts:
            return []

        # combine the silence we detected into ranges (start ms - end ms)
        silent_ranges = []

        prev_i = silence_starts.pop(0)
        current_range_start = prev_i

        for silence_start_i in silence_starts:
            continuous = (silence_start_i == prev_i + seek_step)

            # sometimes two small blips are enough for one particular slice to be
            # non-silent, despite the silence all running together. Just combine
            # the two overlapping silent ranges.
            silence_has_gap = silence_start_i > (prev_i + min_silence_len)

            if not continuous and silence_has_gap:
                silent_ranges.append([current_range_start,
                                    prev_i + min_silence_len])
                current_range_start = silence_start_i
            prev_i = silence_start_i

        silent_ranges.append([current_range_start,
                            prev_i + min_silence_len])

        return silent_ranges

    
    def split_on_silence(self, audio_segment, min_silence_len=1000, silence_thresh=-16, keep_silence=100,
                     seek_step=1):
        """
        keep_silence - (in ms or True/False) leave some silence at the beginning
            and end of the chunks. Keeps the sound from sounding like it
            is abruptly cut off.
            When the length of the silence is less than the keep_silence duration
            it is split evenly between the preceding and following non-silent
            segments.
            If True is specified, all the silence is kept, if False none is kept.
            default: 100ms
        """

        def pairwise(iterable):
            "s -> (s0,s1), (s1,s2), (s2, s3), ..."
            a, b = itertools.tee(iterable)
            next(b, None)
            return zip(a, b)

        if isinstance(keep_silence, bool):
            keep_silence = len(audio_segment) if keep_silence else 0

        output_ranges = [
            [ start - keep_silence, end + keep_silence ]
            for (start,end)
                in self.detect_nonsilent(audio_segment, min_silence_len, silence_thresh, seek_step)
        ]

        for range_i, range_ii in pairwise(output_ranges):
            last_end = range_i[1]
            next_start = range_ii[0]
            if next_start < last_end:
                range_i[1] = (last_end+next_start)//2
                range_ii[0] = range_i[1]
        
        t = [(max(start,0), min(end,len(audio_segment))) for start, end in output_ranges]

        return [
            audio_segment[ max(start,0) : min(end,len(audio_segment)) ]
            for start,end in output_ranges
        ]
    

    def detect_nonsilent(self, audio_segment, min_silence_len=1000, silence_thresh=-16, seek_step=1):
        """
        Returns a list of all nonsilent sections [start, end] in milliseconds of audio_segment.
        Inverse of detect_silent()

        audio_segment - the segment to find silence in
        min_silence_len - the minimum length for any silent section
        silence_thresh - the upper bound for how quiet is silent in dFBS
        seek_step - step size for interating over the segment in ms
        """
        silent_ranges = self.detect_silence(audio_segment, min_silence_len, silence_thresh, seek_step)
        len_seg = len(audio_segment)

        # if there is no silence, the whole thing is nonsilent
        if not silent_ranges:
            return [[0, len_seg]]

        # short circuit when the whole audio segment is silent
        if silent_ranges[0][0] == 0 and silent_ranges[0][1] == len_seg:
            return []

        prev_end_i = 0
        nonsilent_ranges = []
        for start_i, end_i in silent_ranges:
            nonsilent_ranges.append([prev_end_i, start_i])
            prev_end_i = end_i

        if end_i != len_seg:
            nonsilent_ranges.append([prev_end_i, len_seg])

        if nonsilent_ranges[0] == [0, 0]:
            nonsilent_ranges.pop(0)

        return nonsilent_ranges

    def silence_cut_off(self, path, dest):
        sound_file = AudioSegment.from_wav(path)
        filename = path.split('.')[-1]

        audio_chunks = self.split_on_silence(sound_file, 
            # must be silent for at least half a second
            min_silence_len=20,
            # consider it silent if quieter than -16 dBFS
            silence_thresh=-20
        )

        paths = []

        for i, chunk in enumerate(audio_chunks):
            file_path = ''
            file_path = dest + "/" + filename + '-' + str(i) + '.wav';
            chunk.export(file_path, format="wav")
            paths.append(file_path)
        
        return paths

chunk_extension = Chunk()
