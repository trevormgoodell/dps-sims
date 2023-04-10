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
        self._current_time = 0

        self.global_cooldown = 1.5
        self._base_global_cooldown = 1.5
        self._on_gcd = False
        self.gcd_start_time = 0
        self.gcd_end_time = 0

        self._casting = False
        self.cast_start_time = 0
        self.cast_end_time = 0

        self.done = self.max_time == self.current_time

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
        return round(self._current_time, 2)

    @current_time.setter
    def current_time(self, current_time):
        self._current_time = round(current_time, 2)
        if self._current_time >= self.gcd_end_time:
            self.on_gcd = False
        if self._current_time >= round(self.cast_end_time, 2):
            self.casting = False
        self.environment.resource.combat_gain(self.current_time)
        if (current_time // self.max_time) == 1:
            self.done = True


    

