class Buff:
    def __init__(self, start_time, end_time, cooldown, character):
        self.start_time = start_time
        self.end_time = end_time
        self.cooldown = cooldown
        self.character = character
        pass