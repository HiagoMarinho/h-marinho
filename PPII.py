import cv2
import mediapipe as mp
import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
import os
from kivy.core.window import Window

class CustomButton(Button):
    def __init__(self, background_color=(0.1, 0.8, 0.1, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = background_color
        self.color = (1, 1, 1, 1)
        self.font_size = '24sp'
        with self.canvas.before:
            Color(*background_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[0])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.contador = 0
        self.video_files = []
        self.current_video_index = 0
        self.pose = mp.solutions.pose
        self.Pose = self.pose.Pose(min_tracking_confidence=0.7, min_detection_confidence=0.7)
        self.draw = mp.solutions.drawing_utils
        self.sound = SoundLoader.load('count_sound.wav')
        self.check = True
        self.is_playing = False
        self.tp = 0  
        self.fp = 0  
        self.fn = 0
        self.capture = None
        self.video_folder = "c:/Users/hmari/OneDrive/Documentos/CALCULO 1/Nova pasta/videos"  
        Window.size = (640, 480)  
        self.load_video_files()

    def load_video_files(self):
        self.video_files = [f for f in os.listdir(self.video_folder) if f.endswith(('.mp4', '.avi', '.mov'))]

    def build(self):
        self.layout = FloatLayout()
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self.update_rect, pos=self.update_rect)
        button_layout = self.create_button_layout()
        self.layout.add_widget(button_layout)
        return self.layout

    def update_rect(self, *args):
        self.rect.pos = self.layout.pos
        self.rect.size = self.layout.size

    def create_button_layout(self):
        button_layout = FloatLayout()
        iniciar_button = self.create_button('INICIAR', self.start_playing, background_color=(0.3, 1, 0.3, 1))
        parar_button = self.create_button('PARAR', self.stop_playing, background_color=(1, 0.3, 0.3, 1))
        limpar_button = self.create_button('LIMPAR', self.clear_counter, background_color=(0.3, 0.3, 1, 1))
        button_layout.add_widget(iniciar_button)
        button_layout.add_widget(parar_button)
        button_layout.add_widget(limpar_button)

        iniciar_button.size_hint = (0.4, None)
        iniciar_button.size = (200, 80)
        iniciar_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}

        parar_button.size_hint = (0.4, None)
        parar_button.size = (200, 80)
        parar_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        limpar_button.size_hint = (0.4, None)
        limpar_button.size = (200, 80)
        limpar_button.pos_hint = {'center_x': 0.5, 'center_y': 0.3}

        return button_layout

    def clear_counter(self, instance):
        self.contador = 0
        self.tp = 0
        self.fp = 0
        self.fn = 0

    def create_button(self, text, on_press, background_color=(0.1, 0.8, 0.1, 1)):
        btn = CustomButton(text=text, size_hint=(None, None), width=200, height=80, background_color=background_color)
        btn.bind(on_press=on_press)
        return btn

    def start_playing(self, instance):
        if not self.is_playing and self.video_files:
            self.current_video_index = 0
            self.capture = cv2.VideoCapture(os.path.join(self.video_folder, self.video_files[self.current_video_index]))
            Clock.schedule_interval(self.update, 1.0 / 30.0)
            self.is_playing = True

    def stop_playing(self, instance):
        if self.capture:
            self.capture.release()
            self.capture = None
        Clock.unschedule(self.update)
        self.show_results()
        self.is_playing = False
        cv2.destroyAllWindows()

    def show_results(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        precision = self.calculate_precision()
        recall = self.calculate_recall()
        mAP = self.calculate_mAP()

        result_label = Label(text=f'Total de Polichinelos: {self.contador}\n'
                                  f'Precisão: {precision:.2f}\n'
                                  f'Recall: {recall:.2f}\n'
                                  f'mAP: {mAP:.2f}', size_hint=(1, 0.5))
        close_button = Button(text='Fechar', size_hint=(1, None), height=40)
        close_button.bind(on_press=lambda x: popup.dismiss())

        content.add_widget(result_label)
        content.add_widget(close_button)

        popup = Popup(title='Resultados', content=content, size_hint=(0.9, 0.4))
        popup.open()

    def update(self, dt):
        if self.capture is None:
            return

        success, img = self.capture.read()
        if not success:
            self.current_video_index += 1
            if self.current_video_index < len(self.video_files):
                self.capture.release()
                self.capture = cv2.VideoCapture(os.path.join(self.video_folder, self.video_files[self.current_video_index]))
            else:
                self.stop_playing(None)
            return

        original_height, original_width = img.shape[:2]
        aspect_ratio = original_width / original_height

        # Calcular novas dimensões mantendo a proporção
        new_width = 880
        new_height = int(new_width / aspect_ratio)

        if new_height > 660:
            new_height = 660
            new_width = int(new_height * aspect_ratio)

        img = cv2.resize(img, (new_width, new_height))
        img = cv2.copyMakeBorder(img, 0, 660 - new_height, 0, 880 - new_width, cv2.BORDER_CONSTANT, value=(255, 255, 255))

        videoRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.Pose.process(videoRGB)

        if results.pose_landmarks:
            self.process_landmarks(results, img)

        self.draw.draw_landmarks(img, results.pose_landmarks, self.pose.POSE_CONNECTIONS)

        start_point = (0, 70)
        end_point = (270, 0)
        cv2.rectangle(img, start_point, end_point, (255, 0, 0), -1)
        texto = f'Contador: {self.contador}'
        cv2.putText(img, texto, (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

        cv2.imshow('Resultado', img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.stop_playing(None)

    def process_landmarks(self, results, img):
        h, w, _ = img.shape

        if results.pose_landmarks:
            peDY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_FOOT_INDEX].y * h)
            peDX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_FOOT_INDEX].x * w)
            peEY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_FOOT_INDEX].y * h)
            peEX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_FOOT_INDEX].x * w)
            moDY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_INDEX].y * h)
            moDX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_INDEX].x * w)
            moEY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_INDEX].y * h)
            moEX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_INDEX].x * w)

            self.count_polichinelo(moDX, moDY, moEX, moEY, peDX, peDY, peEX, peEY)

    def count_polichinelo(self, moDX, moDY, moEX, moEY, peDX, peDY, peEX, peEY):
        distMO = math.hypot(moDX - moEX, moDY - moEY)
        distPE = math.hypot(peDX - peEX, peDY - peEY)

        LIMITE_DISTANCIA_MAO = 75
        LIMITE_DISTANCIA_PE = 75

        if distMO <= LIMITE_DISTANCIA_MAO and distPE >= LIMITE_DISTANCIA_PE:
            if self.check:
                self.tp += 1
                self.contador += 1
                self.update_sound()
                self.check = False
        else:
            if distMO > LIMITE_DISTANCIA_MAO and distPE < LIMITE_DISTANCIA_PE:
                self.check = True
            else:
                self.fp += 1

    def calculate_precision(self):
        if self.tp + self.fp == 0:
            return 0
        return self.tp / (self.tp + self.fp)

    def calculate_recall(self):
        if self.tp + self.fn == 0:
            return 0
        return self.tp / (self.tp + self.fn)

    def calculate_mAP(self):
        precision = self.calculate_precision()
        return precision

    def update_sound(self):
        if self.sound:
            self.sound.play()

if __name__ == '__main__':
    MainApp().run()
