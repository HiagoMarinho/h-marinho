import cv2
import mediapipe as mp
import math
import csv  # Importar a biblioteca CSV
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle


# Classe personalizada para estilizar botões
class CustomButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0.1, 0.8, 0.1, 1)  # Verde vibrante
        self.color = (1, 1, 1, 1)  # Cor do texto branca
        self.font_size = '24sp'
        with self.canvas.before:
            Color(0.1, 0.8, 0.1, 1)  # Fundo verde vibrante
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[0])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        if args:
            self.rect.pos = self.pos
            self.rect.size = self.size

class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.contador = 0
        self.check_polichinelo = True
        self.check_flexao = True
        self.check_agachamento = True
        self.capture = None
        self.exercicio_atual = "Polichinelo"
        self.pose = mp.solutions.pose
        self.Pose = self.pose.Pose(min_tracking_confidence=0.7, min_detection_confidence=0.7)
        self.draw = mp.solutions.drawing_utils
        self.sound = SoundLoader.load('count_sound.wav')  # Adicione um som de contagem aqui

    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=1, spacing=10)
        
        # Adicionando um Canvas para o fundo
        with self.layout.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Fundo claro
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)

        self.layout.bind(size=self.update_rect, pos=self.update_rect)

        self.label = Label(text='Contador de Exercícios: 0', font_size='40sp', color=(0, 0, 0, 1))  # Texto preto
        self.layout.add_widget(self.label)

        # Spinner com cores relacionadas a fitness
        self.spinner = Spinner(
            text='Escolha o Exercício',
            values=('Polichinelo', 'Flexão', 'Agachamento'),
            size_hint=(None, None),
            size=(400, 90),
            background_color=(0.2, 0.2, 0.8, 1),  # Azul
            color=(1, 1, 1, 1),  # Texto branco
            font_size='24sp',
            pos_hint={'center_x': 0.5},
            padding=(0, 10)  # Centralizar no eixo X
        )
        self.spinner.bind(text=self.on_exercicio_selected)
        self.layout.add_widget(self.spinner)

        # Layout horizontal para os botões com espaçamento
        button_layout = BoxLayout(
            orientation='horizontal', 
            spacing=50,  # Espaçamento entre os botões
            size_hint=(0.5, None), 
            size=(100, 200),  # Defina uma altura maior para incluir espaçamento
            pos_hint={'center_x': 0.5, 'center_y': 0.5}, 
            padding=(30, 40)  # Padding superior e inferior
        )

        # Botão de Iniciar com estilo personalizado
        btn_start = CustomButton(
           text='INICIAR',
           size_hint=(None, None),  # Ocupa toda a altura do layout
           width=200,
           height=80
        )
        btn_start.bind(on_press=self.start_counting)
        button_layout.add_widget(btn_start)  # Adiciona o botão ao layout horizontal

        # Botão de Parar com estilo personalizado
        btn_stop = CustomButton(
           text='PARAR',
           size_hint=(None, None),  # Ocupa toda a altura do layout
           width=200,
           height=80
        )
        btn_stop.bind(on_press=self.stop_counting)
        button_layout.add_widget(btn_stop)  # Adiciona o botão ao layout horizontal

        # Adiciona o layout dos botões ao layout principal
        self.layout.add_widget(button_layout)

        return self.layout

    def update_rect(self, *args):
        self.rect.pos = self.layout.pos
        self.rect.size = self.layout.size

    def on_exercicio_selected(self, spinner: Spinner, text: str):
        self.exercicio_atual = text
        self.contador = 0  # Reseta o contador ao mudar de exercício
        self.label.text = f'Contador de Exercícios: {self.contador}'

    def start_counting(self, instance: Button):
        self.capture = cv2.VideoCapture(0)  # Usar a webcam
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Largura
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Altura
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS

    def stop_counting(self, instance: Button):
        if self.capture:
            self.capture.release()
            self.capture = None
        Clock.unschedule(self.update)
        self.show_results()
        self.save_data()  # Chama a função para salvar os dados

    def show_results(self):
        content = Label(text=f'Total de {self.exercicio_atual}: {self.contador}', size_hint=(1, 0.5))
        popup = Popup(title='Resultados', content=content, size_hint=(0.9, 0.4))
        popup.open()

    def update(self, dt):
        if self.capture is None:
            return

        success, img = self.capture.read()
        if not success:
            return

        # Processamento de imagem
        videoRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.Pose.process(videoRGB)

        # Verificar se os landmarks foram detectados
        if results.pose_landmarks:
            self.process_landmarks(results, img)

        # Desenhar os landmarks
        self.draw.draw_landmarks(img, results.pose_landmarks, self.pose.POSE_CONNECTIONS)

        cv2.imshow('Resultado', img)

        # Para fechar a janela do OpenCV com 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.capture.release()
            cv2.destroyAllWindows()
            self.stop_counting(None)

    def process_landmarks(self, results, img):
        h, w, _ = img.shape

        # Extração de coordenadas das mãos e pés
        moDY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_WRIST].y * h)
        moDX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_WRIST].x * w)
        moEY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_WRIST].y * h)
        moEX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_WRIST].x * w)

        peDY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_FOOT_INDEX].y * h)
        peDX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_FOOT_INDEX].x * w)
        peEY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_FOOT_INDEX].y * h)
        peEX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_FOOT_INDEX].x * w)

        if self.exercicio_atual == "Polichinelo":
            self.count_polichinelo(moDX, moDY, moEX, moEY, peDX, peDY, peEX, peEY)

        elif self.exercicio_atual == "Flexão":
            self.count_flexao(moDY, moEY)

        elif self.exercicio_atual == "Agachamento":
            self.count_agachamento(moDY, moEY)

    def count_polichinelo(self, moDX, moDY, moEX, moEY, peDX, peDY, peEX, peEY):
        if moDY < peDY and moEY < peEY and self.check_polichinelo:
            self.contador += 1
            self.check_polichinelo = False
            self.label.text = f'Contador de Exercícios: {self.contador}'
            if self.sound:  # Reproduz som de contagem
                self.sound.play()
        elif moDY > peDY and moEY > peEY:
            self.check_polichinelo = True

    def count_flexao(self, moDY, moEY):
        if moEY < moDY and self.check_flexao:
            self.contador += 1
            self.check_flexao = False
            self.label.text = f'Contador de Exercícios: {self.contador}'
            if self.sound:  # Reproduz som de contagem
                self.sound.play()
        elif moEY > moDY:
            self.check_flexao = True

    def count_agachamento(self, moDY, moEY):
        if moEY < moDY and self.check_agachamento:
            self.contador += 1
            self.check_agachamento = False
            self.label.text = f'Contador de Exercícios: {self.contador}'
            if self.sound:  # Reproduz som de contagem
                self.sound.play()
        elif moEY > moDY:
            self.check_agachamento = True

    # Função para salvar os dados em um arquivo CSV
    def save_data(self):
        with open('historico_exercicios.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.exercicio_atual, self.contador])  # Salva o exercício e o contador

if __name__ == '__main__':
    MainApp().run()
