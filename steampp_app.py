import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
from gensim.models import Word2Vec
from scipy.io import mmread
from PyQt5.QtGui import *
import pickle
from PyQt5.QtCore import QStringListModel


form_window = uic.loadUiType('./steampp.ui')[0]
recommend_window = uic.loadUiType("./dialog.ui")[0]


class Exam(QWidget, form_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 이미지 넣기---------------------------------------------------
        self.label_2.setPixmap(QPixmap("./steam.jpg"))
        self.label_2.setScaledContents(True)

        self.label_4.setPixmap(QPixmap("./DD.png"))
        self.label_4.setScaledContents(True)

        self.label_5.setPixmap(QPixmap("./Ro.png"))
        self.label_5.setScaledContents(True)

        # -------------------------------------------------------------
        self.Tfidf_matrix = mmread('./models/Tfidf_review.mtx').tocsr()

        with open('./models/tfidf.pickle', 'rb') as f:
            self.Tfidf = pickle.load(f)

        self.embedding_model = Word2Vec.load('./models/word2vec_reviews.model')
        self.df_reviews = pd.read_csv('./games_with_review_and_genre.csv')

        # --------- 게임 제목 리스트를 콤보 박스에 넣기 ---------------------
        self.titles = list(self.df_reviews['titles'])
        self.titles.sort()
        
        self.titles.insert(0, "게임 선택")

        combobox_model = self.cmb_gamelist.model()
        for title in self.titles:
            item = QStandardItem(title)
            item.setForeground(QColor(255, 255, 255))
            item.setBackground(QColor(50, 53, 60))
            combobox_model.appendRow(item)

        # ---------- 장르 리스트를 콤보 박스에 넣기 ------------------------
        self.genres = list(self.df_reviews["genres"])
        genres = []

        for genres_data in self.genres:
            # for genre in genres_data.strip("[]").split(", "):
            #     genres.append(genre.strip("\'"))
            for genre in eval(genres_data):
                genres.append(genre)

        set_genres = set(genres)
        list_genres = list(set_genres)
        list_genres.sort()
        list_genres.insert(0, "장르 미선택")

        genre_model = self.cmb_genrelist.model()
        for genre in list_genres:
            item = QStandardItem(genre)
            item.setForeground(QColor(255, 255, 255))
            item.setBackground(QColor(50, 53, 60))
            genre_model.appendRow(item)

        # --------- 자동 완성 ----------------------------------
        model = QStringListModel()
        model.setStringList(self.titles)
        completer = QCompleter()
        completer.setModel(model)
        self.le_keyword.setCompleter(completer)

        self.cmb_gamelist.currentIndexChanged.connect(self.combobox_slot)
        self.btn_recommendation.clicked.connect(self.btn_slot)

    def btn_slot(self):
        key_word = self.le_keyword.text()

        print(self.cmb_genrelist.currentText())
        print(key_word)

        if key_word in self.titles:  # 게임 타이틀이 입력된 경우
            recommendation = self.recommendatio_by_movie_title(key_word)
        else:
            if self.cmb_genrelist.currentText() == "장르 미선택":
                recommendation = self.recommendation_by_keyword(key_word)
            else:
                # 추천중 선택한 장르가 있는 게임만 출력
                print(f"{self.cmb_genrelist.currentText()}가 선택됨")
                recommendations = self.recommendation_by_keyword(key_word)  
                if recommendations != "그럼 게임 없어요...":
                    recommend_with_genre = ""
                    for temp_reco in recommendations.split("\n"):  # 추천 개별 마다 실행
                        print(temp_reco)
                        game_idx = self.df_reviews[self.df_reviews['titles'] == temp_reco].index[0]  # 인덱스를 찾음
                        if self.cmb_genrelist.currentText() in eval(self.df_reviews.at[game_idx, "genres"]):  
                            # 현재 선택한 장르가 추천한 게임의 장르와 같은 경우만 추천
                            recommend_with_genre = recommend_with_genre + "\n" + temp_reco
                    print(recommend_with_genre)

                    if recommend_with_genre == "":  # 장르와 추천한 게임이 맞지 않는 경우
                        recommendation = "조건을 만족하는 게임이 없습니다."
                    else:
                        recommendation = recommend_with_genre
                else:
                    recommendation = recommendations

        secondwindow = secondWindow(recommendation)

        secondwindow.exec_()

        # self.lbl_recommendation.setText(recommendation)

    def combobox_slot(self):
        title = self.cmb_gamelist.currentText()
        
        if title != "게임 선택":
            print(title)
            recommendation = self.recommendation_by_movie_title(title)

            print(recommendation)
            # self.lbl_recommendation.setText(recommendation)
            secondwindow = secondWindow(recommendation)  # 새 창 객체 생성

            secondwindow.exec_()  # 새창 실행

    def recommendation_by_keyword(self, key_word):
        try:
            sim_word = self.embedding_model.wv.most_similar(key_word, topn=10)
        except:
            return '그럼 게임 없어요...'

        words = [key_word]

        for word, _ in sim_word:
            words.append(word)

        sentence = []
        count = 10
        for word in words:
            sentence = sentence + [word] * count
            count -= 1

        sentence = ' '.join(sentence)

        print(sentence)

        sentence_vec = self.Tfidf.transform([sentence])
        cosine_sim = linear_kernel(sentence_vec, self.Tfidf_matrix)
        recommendation = self.getRecommendation(cosine_sim)
        recommendation = '\n'.join(list(recommendation))

        return recommendation

    def recommendation_by_movie_title(self, title):
        movie_idx = self.df_reviews[self.df_reviews['titles'] == title].index[0]
        cosine_sim = linear_kernel(self.Tfidf_matrix[movie_idx], self.Tfidf_matrix)
        recommendation = self.getRecommendation(cosine_sim)

        recommendation = "\n".join(list(recommendation))

        return recommendation

    def getRecommendation(self, cosine_sim):
        simScore = list(enumerate(cosine_sim[-1]))
        simScore = sorted(simScore, key=lambda x: x[1], reverse=True)
        simScore = simScore[:11]
        movieIdx = [i[0] for i in simScore]
        recmovieList = self.df_reviews.iloc[movieIdx, 0]

        return recmovieList[1:]


class secondWindow(QDialog, recommend_window):  # 새 창을 위한 클래스
    # widget 객체는 widget을 컨트롤 할수 없기 때문에 dialog를 사용
    def __init__(self, recommendation):  # 매개 변수를 이용한 생성자
        super(secondWindow, self).__init__()
        self.setupUi(self)
        self.show()

        print(recommendation)
        self.label_image.setPixmap(QPixmap("./ssteam.png"))
        self.label_image.setScaledContents(True)

        self.game_df = pd.read_csv("./steam.csv")

        linked_list = []

        for reco in recommendation.split("\n"):
            game_idx = self.game_df[self.game_df['titles'] == reco].index[0]

            linked_list.append(f'<a href="{self.game_df.at[game_idx, "gamelinks"]}">{reco}</a>')

        view_text = "<br>".join(linked_list)
        print(view_text)
        self.lbl_recommendation.setOpenExternalLinks(True)
        self.lbl_recommendation.setText(view_text)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = Exam()
    mainWindow.show()
    sys.exit(app.exec_())
