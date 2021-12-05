from typing import List, Dict
from datetime import timedelta, datetime
import numpy as np
import pandas as pd
import nltk.stem as st
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import math
import time
from app_folder.logic.ukrainian_stemmer import UkrainianStemmer

from config import MINDUR_HRS

class Scheduling:
    def __init__(self):
        english_stemmer = st.SnowballStemmer('english')

        class StemmedCountVectorizer(CountVectorizer):
            def build_analyzer(self):
                analyzer = super(StemmedCountVectorizer, self).build_analyzer()
                return lambda doc: ([english_stemmer.stem(UkrainianStemmer(w).stem_word()) for w in analyzer(doc)])

        self.stemmed_vectorizer = StemmedCountVectorizer(analyzer='word', max_features=50)
        self.hashtag_vectorizer = CountVectorizer(analyzer='word', max_features=15)

    def tasksScheduling(self, tasks: List[Dict], previousTasks: List[Dict]) -> List[Dict]:
        if len(tasks) == 0:
            raise ValueError('Got nothing')
        preparedTasksDF = self.tasksPreparation(tasks, previousTasks)
        devidedTasksDF = self.devide_tasks(preparedTasksDF)
        order = self.blank_algo(devidedTasksDF)
        return self.aggreagate(order, devidedTasksDF)

    def tasksPreparation(self, tasks: List[Dict], previousTasks: List[Dict]) -> pd.DataFrame:
        if len(previousTasks) > 0:
            tasksDF = pd.DataFrame(tasks)
            previousTasksDF = pd.DataFrame(previousTasks)
            namePrev_features = self.stemmed_vectorizer.fit_transform(previousTasksDF['name'])
            namePrev_features_arr = namePrev_features.toarray()
            name_features = self.stemmed_vectorizer.transform(tasksDF['name'])
            name_features_arr = name_features.toarray()
            name_features_names = self.stemmed_vectorizer.get_feature_names()
            descriptionPrev_features = self.stemmed_vectorizer.fit_transform(previousTasksDF['description'])
            descriptionPrev_features_arr = descriptionPrev_features.toarray()
            description_features = self.stemmed_vectorizer.transform(tasksDF['description'])
            description_features_arr = description_features.toarray()
            descriptionPrev_hashtag_features = self.hashtag_vectorizer.fit_transform(previousTasksDF['hashtags'])
            descriptionPrev_hashtag_features_arr = descriptionPrev_hashtag_features.toarray()
            description_hashtag_features = self.hashtag_vectorizer.transform(tasksDF['hashtags'])
            description_hashtag_features_arr = description_hashtag_features.toarray()

            previousTasksDF_prepared = pd.concat([previousTasksDF.drop(['description', 'hashtags', 'deadline', 'completed_at',
                                                                        'result', 'start_time', 'duration_of_completing',
                                                                        'can_be_performed_after_dd', 'importance', 'name'], axis=1),
                                                  pd.DataFrame(namePrev_features_arr, columns=name_features_names),
                                                  pd.DataFrame(descriptionPrev_features_arr, columns=self.stemmed_vectorizer.get_feature_names()),
                                                  pd.DataFrame(descriptionPrev_hashtag_features_arr, columns=self.hashtag_vectorizer.get_feature_names())
                                                  ], axis=1)
            previousTasksDF_prepared.set_index('id', inplace=True)

            tasksDF_prepared = pd.concat([tasksDF.drop(['description', 'hashtags', 'deadline', 'completed_at', 'result',
                                                        'start_time', 'duration_of_completing',
                                                        'can_be_performed_after_dd', 'importance', 'name'], axis=1),
                                          pd.DataFrame(name_features_arr, columns=name_features_names),
                                          pd.DataFrame(description_features_arr, columns=self.stemmed_vectorizer.get_feature_names()),
                                          pd.DataFrame(description_hashtag_features_arr, columns=self.hashtag_vectorizer.get_feature_names())], axis=1)
            tasksDF_prepared.set_index('id', inplace=True)
            #increase: -1, 0, 1
            y_train = pd.Series(previousTasksDF.apply(lambda x: 1 if not x['result'] or x['deadline'] < x['completed_at'] else -1 \
                if (x['deadline'] - x['completed_at'])/x['duration_of_completing'] > 0.5 else 0, axis=1))
            nb = MultinomialNB()
            nb.fit(previousTasksDF_prepared, y_train)
            y_pred = nb.predict(tasksDF_prepared)
            tasksDF['y_pred'] = y_pred
            tasksDF['start_time'] = tasksDF['start_time'].fillna(time.time())
            tasksDF['estimated_dur'] = tasksDF.apply(lambda x: x['duration_of_completing'] if x['y_pred'] == 0 or
                            round((x['deadline'] - x['start_time']), 3) == round(x['duration_of_completing'],3) else
                            x['duration_of_completing']*0.8 if x['y_pred'] == -1 else
                            x['duration_of_completing']*1.3, axis=1)
            tasksDF['estimated_gap'] = tasksDF.apply(lambda x: int(x['duration_of_completing']*0.2) if x['y_pred'] == -1 else
                                                     int(x['duration_of_completing']*0.4) if x['y_pred'] == 1 else
                                                     int(x['duration_of_completing']*0.3), axis=1)

            del namePrev_features_arr, name_features_arr, descriptionPrev_features_arr, description_features_arr, \
                descriptionPrev_hashtag_features_arr, description_hashtag_features_arr
            return tasksDF
        else:
            tasksDF = pd.DataFrame(tasks)
            tasksDF['start_time'] = tasksDF['start_time'].fillna(time.time())
            tasksDF['estimated_dur'] = tasksDF['duration_of_completing']
            tasksDF['estimated_gap'] = tasksDF['duration_of_completing'].map(lambda x: int(x*0.3))
            return tasksDF



    '''
     Тут створюємо покарання за невиконання тасків.
     Для тих тасків, які робляться весь час між конкретними моментами і є важливими, воно найбільше - 1000. 
     Далі йдуть таски, що є важливими, проте можуть бути зроблені впродовж часу (дюрейшн < дед-старт). 
     Покарання їм = 800. Далі неважливі таски, що мають бути виконані в конкретний момент. Покарання = 600. 
     Потім ті таски, що важливі, але можуть бути виконані після дд. Покарання їм = 400. 
     Після цього таски, що неважливі, але мають бути виконані до дд. Покарання = 200. 
     І неважливі таски після дд з покаранням = 0.
    '''
    @staticmethod
    def calc_next_part_of_hour():
        thisTime = datetime.now()
        nextPartOfHour = thisTime.replace(second=0, microsecond=0, minute=0, hour=thisTime.hour)
        halfsCount = ((thisTime.minute) / 60 + (thisTime.second) / 3600 + (
            thisTime.microsecond) / 36000000) / MINDUR_HRS
        td = timedelta(hours=math.ceil(halfsCount)) * MINDUR_HRS
        nextPartOfHour += td
        return nextPartOfHour

    @staticmethod
    def calc_deadline_in_mindur(x):
        nextPartOfHour = Scheduling.calc_next_part_of_hour()
        basicHoursPartsBetween = math.ceil(round((datetime.fromtimestamp(x) - nextPartOfHour).total_seconds() / 3600, 2) / MINDUR_HRS)
        prevPartOfHourBeforeDD = nextPartOfHour + timedelta(hours=(basicHoursPartsBetween - 1)*MINDUR_HRS)
        startTimeHours = 6
        endTimeHours = 18
        nightsBetween = ((datetime.fromtimestamp(x) - timedelta(days=1)).day - (nextPartOfHour + timedelta(days=1)).day)
        # nightsBetween = nightsBetween if nightsBetween >= 0 else 0
        additionalHoursPartsBetween = 0
        if nextPartOfHour.hour >= startTimeHours and nextPartOfHour.hour < endTimeHours:
            nightsBetween += 1
        elif nextPartOfHour.hour < startTimeHours:
            nightsBetween += 1
            additionalHoursPartsBetween += (startTimeHours - nextPartOfHour.hour)/MINDUR_HRS - 1 if nextPartOfHour.minute == 60*MINDUR_HRS else 0
        else:
            additionalHoursPartsBetween += (startTimeHours - 24 + nextPartOfHour.hour)/MINDUR_HRS - 1 if nextPartOfHour.minute == 60*MINDUR_HRS else 0
        #
        #deadline = datetime.fromtimestamp(x)
        if prevPartOfHourBeforeDD.hour >= startTimeHours and prevPartOfHourBeforeDD.hour < endTimeHours:
            nightsBetween += 1
        elif prevPartOfHourBeforeDD.hour < startTimeHours:
            additionalHoursPartsBetween += (24 - endTimeHours + prevPartOfHourBeforeDD.hour)/MINDUR_HRS
            additionalHoursPartsBetween += 1 if nextPartOfHour.minute == 60 * MINDUR_HRS else 0
        else:
            nightsBetween += 1
            additionalHoursPartsBetween += (prevPartOfHourBeforeDD.hour - endTimeHours)/MINDUR_HRS
            additionalHoursPartsBetween += 1 if nextPartOfHour.minute == 60*MINDUR_HRS else 0
        return basicHoursPartsBetween - nightsBetween*(24 - endTimeHours + startTimeHours)/MINDUR_HRS - additionalHoursPartsBetween

    def devide_tasks(self, tasks: pd.DataFrame):
        tasks['times'] = tasks['estimated_dur'].map(lambda x: math.ceil(round((datetime.fromtimestamp(x) - datetime(1970, 1, 1))
                                                                       .total_seconds()/3600, 2)/MINDUR_HRS))


        tasks['punishment'] = tasks.apply(lambda x: 0 if round((x['deadline'] - x['start_time']), 3) < round(x['estimated_dur'],3) else
                            1000 if x['importance'] and round((x['deadline'] - x['start_time']), 3) == round(x['estimated_dur'],3) else
                            800 if x['importance'] and not x['can_be_performed_after_dd'] else
                            600 if not x['importance'] and round((x['deadline'] - x['start_time']), 3) == round(x['estimated_dur'],3) else
                            400 if x['importance'] and x['can_be_performed_after_dd'] else
                            200 if not x['importance'] and x['can_be_performed_after_dd'] else
                            0, axis=1)
        #translate to half of hours
        tasks['deadline_in_midur'] = tasks['deadline'].map(Scheduling.calc_deadline_in_mindur)
        tasks['start_time'] = tasks['start_time'].map(Scheduling.calc_deadline_in_mindur)
        tasks = tasks.loc[tasks.index.repeat(tasks['times'])].reset_index(drop=True)
        tasks['subtask_id'] = pd.Series(range(len(tasks)))
        tasks['subtask_id_dummy'] = pd.Series(range(len(tasks)))
        tasks.set_index('subtask_id', inplace=True)
        #change_tasks_deadlines
        return tasks


    def blank_algo(self, tasks: pd.DataFrame) -> np.array(int):
        tasks.sort_values(by=['punishment'], ascending=[False], inplace=True)
        resLen = max(int(tasks['deadline_in_midur'].max()), len(tasks))
        res = np.full(resLen, -1)
        waiting_to_try = []
        for i in range(len(tasks)):
            if not(tasks.loc[i, 'can_be_performed_after_dd']) and len(waiting_to_try) > 0:
                # deal with the list and try to insert it's values
                while len(waiting_to_try) > 0:
                    elemId = waiting_to_try.pop(0)
                    for j in range(tasks.loc[elemId, 'deadline_in_midur'] + 1, resLen):
                        if res[j] == -1:
                            res[j] = tasks.loc[elemId, 'subtask_id_dummy']
                            break
            dead = int(tasks.loc[i, 'deadline_in_midur'])
            gap = int(tasks.loc[i, 'estimated_gap'])
            start = int(tasks.loc[i, 'start_time'])
            foundPlace = False
            for j in reversed(range(start, dead - gap)):
                if res[j] == -1:
                    foundPlace = True
                    res[j] = tasks.loc[i, 'subtask_id_dummy']
                    break
            if not foundPlace:
                for j in range(dead-gap, dead + 1):
                    if res[j] == -1:
                        foundPlace = True
                        res[j] = tasks.loc[i, 'subtask_id_dummy']
                        break
            if not foundPlace:
                if tasks.loc[i, 'can_be_performed_after_dd']:
                    waiting_to_try.append(i)
                else:
                    counter = 0
                    for j in reversed(range(dead)):
                        if tasks.loc[res[j], 'id'] == tasks.loc[i, 'id']:
                            counter += 1
                            res[j] = -1
                            if counter == tasks.loc[i, 'times']:
                                break
                    while i + 1 < len(tasks) and tasks.loc[i+1, 'id'] == tasks.loc[i, 'id']:
                        i += 1
        return res

    def aggreagate(self, schedule: np.array(int), tasks: pd.DataFrame) -> List[Dict]:
        result = []
        nextPartOfHour = Scheduling.calc_next_part_of_hour()
        startTimeHours = 6
        endTimeHours = 18
        start = datetime(year=nextPartOfHour.year, month=nextPartOfHour.month, day=nextPartOfHour.day,
                 hour=(nextPartOfHour.hour if nextPartOfHour.hour >= startTimeHours and nextPartOfHour.hour < endTimeHours else
                       startTimeHours if nextPartOfHour.hour < startTimeHours else endTimeHours),
                 minute=(nextPartOfHour.minute if nextPartOfHour.hour >= startTimeHours and nextPartOfHour.hour < endTimeHours else
                         0))
        end = datetime(year=nextPartOfHour.year, month=nextPartOfHour.month, day=nextPartOfHour.day, hour=endTimeHours)
        count = (end-start)/timedelta(hours=MINDUR_HRS)
        if count == 0:
            return []
        if schedule[0] == -1:
            prevObj = {'id_task': -1, 'start_time': start, 'end_time': start + timedelta(minutes=30)}
        else:
            id_task = tasks[schedule[0]]
            prevObj = {'id_task': id_task, 'start_time': start, 'end_time': start + timedelta(minutes=30)}
        for i in range(1, int(count)):
            if (schedule[i] == -1 and prevObj['id_task'] == -1) or tasks.loc[schedule[i], 'id'] == prevObj['id_task']:
                prevObj['end_time'] = prevObj['end_time'] + timedelta(minutes=30)
            else:
                result.append({'id_task': prevObj['id_task'], 'recommended_time':
                    f'{(prevObj["start_time"].hour+2):02d}:{prevObj["start_time"].minute:02d}-{(prevObj["end_time"].hour+2):02d}:{prevObj["end_time"].minute:02d}'})
                prevObj['id_task'] = tasks.loc[schedule[i], 'id']
                prevObj['start_time'] = start + i*timedelta(minutes=30)
                prevObj['end_time'] = start + (i+1)*timedelta(minutes=30)
        result.append({'id_task': prevObj['id_task'], 'recommended_time':
            f'{(prevObj["start_time"].hour + 2):02d}:{prevObj["start_time"].minute:02d}-{(prevObj["end_time"].hour + 2):02d}:{prevObj["end_time"].minute:02d}'})

        return result

if __name__ == '__main__':

    # print(sc.blank_algo(
    #     np.array(range(7)),
    #     np.array([10, 5, 3, 8, 2, 11, 2]),
    #     np.array([4, 2, 1, 4, 1, 1, 2])
    # ))
    # print(sc.blank_algo(
    #     np.array(range(4)),
    #     np.array([10, 5, 1, 8]),
    #     np.array([4, 2, 1, 4])
    # ))
    # print(sc.blank_algo(
    #     np.array(range(7)),
    #     np.array([6, 5, 3, 8, 2, 4, 2]),
    #     np.array([4, 2, 1, 4, 1, 1, 2])
    # ))

    train_data = []
    # train_data = [{'id': 1, 'description': 'Агов, хлопче!. 14.4', 'hashtags': '#one #two',
    #          'deadline': 3, 'completed_at': 2, 'result': True, 'start_time': 0, 'duration_of_completing': 1,
    #               'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
    #         {'id': 2, 'description': 'Юхууу, вперед, хлоп. 13.3', 'hashtags': '#three #two',
    #          'deadline': 4, 'completed_at': None, 'result': False, 'start_time': 1, 'duration_of_completing': 1,
    #               'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
    #         {'id': 3, 'description': 'Я буду скоро йти назад. 16.6', 'hashtags': '#one',
    #          'deadline': 2, 'completed_at': 2, 'result': True, 'start_time': 0, 'duration_of_completing': 1,
    #               'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
    #         {'id': 4, 'description': 'Назад чи мною вийде піти, ага?', 'hashtags': '#two',
    #          'deadline': 1, 'completed_at': 2, 'result': True, 'start_time': 0, 'duration_of_completing': 1,
    #               'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True}
    # ]
    test_data = [{'id': 1, 'description': 'Агов, хлопче!. 14.4', 'hashtags': '#one #one',
                'deadline': 1638869999.12, 'completed_at': None, 'result': None, 'start_time': None,#1638669999.12,
                  'duration_of_completing': 1,
                  'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
                 {'id': 2, 'description': 'Гей, Друже!. 14,4', 'hashtags': '#one #two',
                  'deadline': 1638739999.12, 'completed_at': None, 'result': None, 'start_time': None,  # 1638669999.12,
                  'duration_of_completing': 2,
                  'name': 'Another important thing', 'can_be_performed_after_dd': True, 'importance': True}
                 ]
    sc = Scheduling()
    print(sc.tasksScheduling(test_data, train_data))
    # print(sc.calc_deadline_in_mindur(1638669999.12))