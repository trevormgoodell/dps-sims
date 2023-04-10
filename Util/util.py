import numpy as np

def DiminishSecondaryStat(stat, stat_value, point_conversion = 1, base_val = 0):
    _thresholds = {
        "Critical Strike": [0, 5400, 7200, 9000, 10800, 14400, 36000],
        "Haste": [0, 5100, 6800, 8500, 10200, 13600, 34000],
        "Mastery": [0, 5220, 6960, 8700, 10440, 13920, 34800],
        "Versatility": [0, 6150, 8200, 10250, 12300, 16400, 41000],
    }
    total_points = 0
    
    thresholds = _thresholds[stat]
    points = [0, 30, 39, 47, 54, 66, 126]

    for i in range(1, len(thresholds)):
        curr_points = points[i] - points[i-1]
        if stat_value > thresholds[i]:
            total_points += curr_points

        else:
            rem_stat = stat_value - thresholds[i-1]
            rem_score = rem_stat / (thresholds[i] - thresholds[i-1])
            total_points += curr_points * rem_score
            break
        
    total_points += base_val

    percent = total_points * point_conversion

    return percent

if __name__ == "__main__":
    print(DiminishSecondaryStat("Critical Strike", 1831, point_conversion = 1, base_val = 5))
    print(DiminishSecondaryStat("Haste", 4504, point_conversion = 1, base_val = 0))
    print(DiminishSecondaryStat("Versatility", 673, point_conversion = 1, base_val = 0))
    print(DiminishSecondaryStat("Mastery", 4196, point_conversion = 0.9, base_val = 7.2))
    print(DiminishSecondaryStat("Mastery", 3653, point_conversion = 0.9, base_val = 7.2))
    

    #print(DiminishSecondaryStat("Mastery", 1993, point_conversion = 1.1, base_val = 8))