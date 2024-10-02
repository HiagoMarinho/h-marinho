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
from kivy.core.window import Window

class CustomButton(Button):
    def __init__(self, background_color=(0.1, 0.8, 0.1, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = background_color
        self.color = (1, 1, 1, 1)  # Cor do texto
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
        self.capture = None
        self.pose = mp.solutions.pose
        self.Pose = self.pose.Pose(min_tracking_confidence=0.7, min_detection_confidence=0.7)
        self.draw = mp.solutions.drawing_utils
        self.sound = SoundLoader.load('count_sound.wav')
        self.check = True
        self.is_counting = False

        Window.size = (300, 500)  # Define o tamanho da janela

    def build(self):
        self.layout = FloatLayout()  # Usando FloatLayout para permitir sobreposição

            # Adicionando cor de fundo
        with self.layout.canvas.before:
             Color(1, 1, 1, 1)  # Branco
             self.rect = RoundedRectangle(size=self.layout.size, pos=self.layout.pos)

        self.layout.bind(size=self.update_rect, pos=self.update_rect)  # Atualiza o retângulo ao redimensionar


        self.label = Label(text='Contador de Exercícios: 0', color=(1, 1, 1, 1))
        self.layout.add_widget(self.label)
        button_layout = self.create_button_layout()
        self.layout.add_widget(button_layout)

        return self.layout
    
    def update_rect(self, *args):
        self.rect.pos = self.layout.pos
        self.rect.size = self.layout.size

    def create_button_layout(self):
        button_layout = FloatLayout()  # Usando FloatLayout para melhor centralização

        iniciar_button = self.create_button('INICIAR', self.start_counting, background_color=(0.3, 1, 0.3, 1))  # Verde
        parar_button = self.create_button('PARAR', self.stop_counting, background_color=(1, 0.3, 0.3, 1))   # Vermelho
        limpar_button = self.create_button('LIMPAR', self.clear_counter, background_color=(0.3, 0.3, 1, 1))  # Azul

        # Adicionando os botões ao layout
        button_layout.add_widget(iniciar_button)
        button_layout.add_widget(parar_button)
        button_layout.add_widget(limpar_button)  # Adicionando o botão de limpar

        # Definindo a posição dos botões
        iniciar_button.size_hint = (0.4, None)
        iniciar_button.size = (200, 80)
        iniciar_button.pos_hint = {'center_x': 0.5, 'center_y': 0.7}

        parar_button.size_hint = (0.4, None)
        parar_button.size = (200, 80)
        parar_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        limpar_button.size_hint = (0.4, None)
        limpar_button.size = (200, 80)
        limpar_button.pos_hint = {'center_x': 0.5, 'center_y': 0.3}  # Posição do botão de limpar

        return button_layout
    
    def clear_counter(self, instance):
       self.contador = 0
       self.update_label()  # Atualiza a label com o contador zerado

    def create_button(self, text, on_press, background_color=(0.1, 0.8, 0.1, 1)):
        btn = CustomButton(text=text, size_hint=(None, None), width=200, height=80, background_color=background_color)
        btn.bind(on_press=on_press)
        return btn

    def start_counting(self, instance):
        if not self.is_counting:
            self.capture = cv2.VideoCapture(0)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            Clock.schedule_interval(self.update, 1.0 / 30.0)
            self.is_counting = True

    def stop_counting(self, instance):
        if self.capture:
            self.capture.release()
            self.capture = None
        Clock.unschedule(self.update)
        self.show_results()
        self.is_counting = False
        cv2.destroyAllWindows()  # Fecha a janela da câmera


    def show_results(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        result_label = Label(text=f'Total de Polichinelos: {self.contador}', size_hint=(1, 0.5))
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
            return

        # Processamento de imagem
        videoRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.Pose.process(videoRGB)

        # Verificar se os landmarks foram detectados
        if results.pose_landmarks:
            self.process_landmarks(results, img)

        # Desenhar os landmarks
        self.draw.draw_landmarks(img, results.pose_landmarks, self.pose.POSE_CONNECTIONS)

        # Mostrar o contador na tela da câmera:
         # Definindo as coordenadas do retângulo
        start_point = (20, 240)
        end_point = (450, 100)
        # Desenhando o retângulo
        cv2.rectangle(img, start_point, end_point, (255, 0, 0), -1)

        # Definindo o texto
        texto = f'Contador: {self.contador}'
        cv2.putText(img, texto, (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)

        cv2.imshow('Resultado', img)

        # Para fechar a janela do OpenCV com 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.stop_counting(None)

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

        print(f'maos {distMO} pes {distPE}')

        LIMITE_DISTANCIA_MAO = 150
        LIMITE_DISTANCIA_PE = 150

        if self.check and distMO <= LIMITE_DISTANCIA_MAO and distPE >= LIMITE_DISTANCIA_PE:
            self.contador += 1
            self.check = False
            self.update_label()

        if distMO > LIMITE_DISTANCIA_MAO and distPE < LIMITE_DISTANCIA_PE:
            self.check = True

    def update_label(self):
        self.label.text = f'Contador de Exercícios: {self.contador}'
        if self.sound:
            self.sound.play()

if __name__ == '__main__':
    MainApp().run()
