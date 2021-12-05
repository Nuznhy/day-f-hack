from typing import List, Dict
from datetime import timedelta, datetime
import numpy as np
import pandas as pd
import nltk.stem as st
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from app_folder.logic.ukrainian_stemmer import UkrainianStemmer


class Scheduling:
    def __init__(self):
        english_stemmer = st.SnowballStemmer('english')

        class StemmedCountVectorizer(CountVectorizer):
            def build_analyzer(self):
                analyzer = super(StemmedCountVectorizer, self).build_analyzer()
                return lambda doc: ([english_stemmer.stem(UkrainianStemmer(w).stem_word()) for w in analyzer(doc)])

        self.stemmed_vectorizer = StemmedCountVectorizer(analyzer='word', max_features=50)
        self.hashtag_vectorizer = CountVectorizer(analyzer='word', max_features=15)

    def tasksScheduling(self, tasks: List[Dict], previousTasks: List[Dict]):
        preparedTasksDF = self.tasksPreparation(tasks, previousTasks)
        devidedTasksDF = self.devide_tasks(preparedTasksDF)

    def tasksPreparation(self, tasks: List[Dict], previousTasks: List[Dict]) -> pd.DataFrame:
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
        tasksDF['estimated_dur'] = tasksDF.apply(lambda x: x['duration_of_completing']*0.8 if x['y_pred'] == -1 else
                                                 x['duration_of_completing']*1.3 if x['y_pred'] == 1 else
                                                 x['duration_of_completing'], axis=1)
        tasksDF['estimated_gap'] = tasksDF.apply(lambda x: x['duration_of_completing']*0.2 if x['y_pred'] == -1 else
                                                 x['duration_of_completing']*0.4 if x['y_pred'] == 1 else
                                                 x['duration_of_completing']*0.3, axis=1)
        return tasksDF


    def devide_tasks(self, tasks: pd.DataFrame):
        tasks['dur_date'] = tasks['estimated_dur'].map(lambda x: (datetime.fromtimestamp(x) - datetime(1900, 1, 1)))
        print(tasks['number'])

    def blank_algo(self, ids: np.array(int), deadlines: np.array(int), punishments: np.array(int), gap:int = 1) -> np.array(int):
        argsToSort = np.argsort(-punishments)
        deadlinesSorted = deadlines[argsToSort]
        punishmentsSorted = punishments[argsToSort]
        idsSorted = ids[argsToSort]
        resLen = np.max(deadlines)
        res = np.full(resLen, -1)
        failed = np.zeros(len(deadlinesSorted))
        for i in range(len(punishmentsSorted)):
            dead = deadlinesSorted[i]
            foundPlace = False
            for j in reversed(range(dead - gap)):
                if res[j] == -1:
                    foundPlace = True
                    res[j] = idsSorted[i]
                    break
            if not foundPlace:
                for j in range(dead-gap, dead + 1):
                    if res[j] == -1:
                        foundPlace = True
                        res[j] = idsSorted[i]
                        break
            if not foundPlace:
                #dependsOnType
                pass
            if not foundPlace:
                failed[idsSorted[i]] = 1
        return res, failed

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


    train_data = [{'id': 1, 'description': 'Агов, хлопче!. 14.4', 'hashtags': '#one #two',
             'deadline': 3, 'completed_at': 2, 'result': True, 'start_time': 0, 'duration_of_completing': 1,
                  'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
            {'id': 2, 'description': 'Юхууу, вперед, хлоп. 13.3', 'hashtags': '#three #two',
             'deadline': 4, 'completed_at': None, 'result': False, 'start_time': 1, 'duration_of_completing': 1,
                  'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
            {'id': 3, 'description': 'Я буду скоро йти назад. 16.6', 'hashtags': '#one',
             'deadline': 2, 'completed_at': 2, 'result': True, 'start_time': 0, 'duration_of_completing': 1,
                  'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True},
            {'id': 4, 'description': 'Назад чи мною вийде піти, ага?', 'hashtags': '#two',
             'deadline': 1, 'completed_at': 2, 'result': True, 'start_time': 0, 'duration_of_completing': 1,
                  'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True}
    ]
    test_data = [{'id': 1, 'description': 'Агов, хлопче!. 14.4', 'hashtags': '#one #one',
             'deadline': 1, 'completed_at': None, 'result': None, 'start_time': 0, 'duration_of_completing': 1,
                  'name': 'Something important', 'can_be_performed_after_dd': True, 'importance': True}]
    sc = Scheduling()
    sc.tasksScheduling(test_data, train_data)