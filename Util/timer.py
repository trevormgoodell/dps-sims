class Timer:
    def __init__(self, max_time, time_step, environment):
        """
        A class that will manage the combat timer and buffs

        inputs:
        max_time = how long to run the simulation for
        time_step = how often the time_step updates
        environment = the environment to attach to
        """
        self.max_time = max_time
        self.time_step = time_step
        self.environment = environment
        self.current_time = 0

        self.global_cooldown = 1.5
        self._on_gcd = False
        self.gcd_start_time = 0
        self.gcd_end_time = 0

        self._casting = False
        self.cast_start_time = 0
        self.cast_end_time = 0

        self.event_table = []

    @property
    def on_gcd(self):
        return self._on_gcd

    @on_gcd.setter
    def on_gcd(self, on_gcd):
        self._on_gcd = on_gcd
        if on_gcd == True:
            self.gcd_start_time = self.current_time
            self.gcd_end_time = self.current_time + self.global_cooldown

    @property
    def casting(self):
        return self._casting

    # Casting is set by passing the "cast time" not a boolean
    @casting.setter
    def casting(self, cast_time):
        self._casting = cast_time > 0
        if self._casting == True:
            self.cast_start_time = self.current_time
            self.cast_end_time = self.current_time + cast_time

    @property
    def current_time(self):
        return self._current_time

    @current_time.setter
    def current_time(self, current_time):
        self._current_time = current_time
        if self._current_time == self.gcd_end_time:
            self.on_gcd = False
        if self._current_time == self.cast_end_time:
            self.casting = 0
        self.resource.combat_gain(self.current_time)

    def add_timer_event(self, timer_event):
        setattr(self.environment, timer_event.stat, getattr(self.environment, timer_event.stat)+timer_event.modifier)
        self.event_table.append(timer_event)

    def update_time(self):
        self.current_time += self.time_step

        old_events = [event for event in self.event_table if event.end_time == self.current_time]

        for timer_event in old_events:
            setattr(self.environment, timer_event.stat, getattr(self.environment, timer_event.stat) - timer_event.modifier)
        
        for event in old_events:
            self.event_table.remove(event)

class TimerEvent:
    def __init__(self, timer, start_time, end_time, stat, modifier):
        """
        The class that represents any sort of effect that requires a timer (e.g. buffs)

        inputs:
        timer = the timer that handles timer_events
        start_time = when the timer_event starts
        end_time = when the timer_event ends
        stat = What stat is getting affected, must be a string and must match attribute name
        modifier = How much the stat is getting affected
        """
        self.timer = timer
        self.start_time = start_time
        self.end_time = end_time
        self.stat = stat
        self.modifier = modifier