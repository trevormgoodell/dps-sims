from Druid.Balance.balance_env_2 import *

env = BalanceDruidEnvironment(
    haste=4504,
    critical_strike=1831,
    versatility=673,
    mastery=4196,
    main_stat=9553
)

print(env.calculate_damage(env.wrath))