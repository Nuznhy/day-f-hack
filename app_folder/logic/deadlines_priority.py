from typing import List, Dict
from datetime import datetime

def deadlines_priority(records: List[Dict]) -> List[int]:
    deadlines = list(map(lambda rec: rec.get('deadline', None), records))
    if None in deadlines:
        raise ValueError('deadline doesn\'t exist')
    lst = [x for x, y in sorted(enumerate(deadlines), key=lambda x: datetime.now() - x[1])]
    return [max(lst) - lst

if __name__=='__main__':
    print(deadlines_priority([
        {'deadline': datetime(2020, 9, 15, 23, 5, 11)},
        {'deadline': datetime(2020, 10, 15, 22, 5, 11)},
        {'deadline': datetime(2020, 9, 15, 23, 5, 10)}
    ]))