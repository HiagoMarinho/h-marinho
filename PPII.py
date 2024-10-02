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

# Classe CustomButton para personalizar a aparência dos botões
class CustomButton(Button):
    def __init__(self, background_color=(0.1, 0.8, 0.1, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = background_color
        self.color = (1, 1, 1, 1)  # Cor do texto do botão
        self.font_size = '24sp'
        with self.canvas.before:
            Color(*background_color)  # Define a cor de fundo do botão
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[0])
        self.bind(pos=self.update_rect, size=self.update_rect)  # Atualiza o retângulo ao redimensionar

    # Atualiza o retângulo de fundo quando o botão muda de tamanho ou posição
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# Classe principal da aplicação
class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.contador = 0  # Contador de exercícios
        self.capture = None  # Variável para captura de vídeo
        self.pose = mp.solutions.pose  # Inicializa o módulo de pose do Mediapipe
        self.Pose = self.pose.Pose(min_tracking_confidence=0.7, min_detection_confidence=0.7)  # Configurações de detecção
        self.draw = mp.solutions.drawing_utils  # Utilitário para desenhar os landmarks
        self.sound = SoundLoader.load('count_sound.wav')  # Carrega o som do contador
        self.check = True  # Variável para controle da contagem
        self.is_counting = False  # Indica se a contagem está ativa
        Window.size = (300, 500)  # Define o tamanho da janela

    # Constrói a interface gráfica
    def build(self):
        self.layout = FloatLayout()  # Layout que permite sobreposição de widgets
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)  # Cor de fundo branca
            self.rect = RoundedRectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self.update_rect, pos=self.update_rect)  # Atualiza o retângulo ao redimensionar
        self.label = Label(text='Contador de Exercícios: 0', color=(1, 1, 1, 1))  # Label para exibir o contador
        self.layout.add_widget(self.label)
        button_layout = self.create_button_layout()  # Cria o layout dos botões
        self.layout.add_widget(button_layout)
        return self.layout
    
    # Atualiza o retângulo de fundo do layout
    def update_rect(self, *args):
        self.rect.pos = self.layout.pos
        self.rect.size = self.layout.size

    # Cria o layout dos botões
    def create_button_layout(self):
        button_layout = FloatLayout()  # Layout para os botões
        # Cria botões para iniciar, parar e limpar
        iniciar_button = self.create_button('INICIAR', self.start_counting, background_color=(0.3, 1, 0.3, 1))
        parar_button = self.create_button('PARAR', self.stop_counting, background_color=(1, 0.3, 0.3, 1))
        limpar_button = self.create_button('LIMPAR', self.clear_counter, background_color=(0.3, 0.3, 1, 1))
        button_layout.add_widget(iniciar_button)
        button_layout.add_widget(parar_button)
        button_layout.add_widget(limpar_button)

        # Define a posição e tamanho dos botões
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
    
    # Limpa o contador
    def clear_counter(self, instance):
        self.contador = 0  # Reseta o contador
        self.update_label()  # Atualiza a label com o contador zerado

    # Cria um botão com texto e ação associada
    def create_button(self, text, on_press, background_color=(0.1, 0.8, 0.1, 1)):
        btn = CustomButton(text=text, size_hint=(None, None), width=200, height=80, background_color=background_color)
        btn.bind(on_press=on_press)  # Vincula a ação ao botão
        return btn

    # Inicia a contagem de exercícios
    def start_counting(self, instance):
        if not self.is_counting:
            self.capture = cv2.VideoCapture(0)  # Inicia a captura de vídeo
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Define a largura do vídeo
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Define a altura do vídeo
            Clock.schedule_interval(self.update, 1.0 / 30.0)  # Atualiza a cada 30 FPS
            self.is_counting = True

    # Para a contagem de exercícios
    def stop_counting(self, instance):
        if self.capture:
            self.capture.release()  # Libera a captura de vídeo
            self.capture = None
        Clock.unschedule(self.update)  # Para a atualização
        self.show_results()  # Exibe os resultados
        self.is_counting = False
        cv2.destroyAllWindows()  # Fecha a janela da câmera

    # Exibe os resultados em um popup
    def show_results(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        result_label = Label(text=f'Total de Polichinelos: {self.contador}', size_hint=(1, 0.5))  # Exibe o total
        close_button = Button(text='Fechar', size_hint=(1, None), height=40)
        close_button.bind(on_press=lambda x: popup.dismiss())  # Fecha o popup ao clicar

        content.add_widget(result_label)
        content.add_widget(close_button)

        popup = Popup(title='Resultados', content=content, size_hint=(0.9, 0.4))  # Cria o popup
        popup.open()  # Abre o popup

    # Atualiza a captura de vídeo e processa os dados
    def update(self, dt):
        if self.capture is None:
            return

        success, img = self.capture.read()  # Lê um quadro da captura
        if not success:
            return

        videoRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Converte o quadro para RGB
        results = self.Pose.process(videoRGB)  # Processa a imagem para detecção de pose

        if results.pose_landmarks:
            self.process_landmarks(results, img)  # Processa os landmarks se encontrados

        self.draw.draw_landmarks(img, results.pose_landmarks, self.pose.POSE_CONNECTIONS)  # Desenha os landmarks

        # Desenha um retângulo de fundo para o contador
        start_point = (20, 240)
        end_point = (450, 100)
        cv2.rectangle(img, start_point, end_point, (255, 0, 0), -1)  # Retângulo azul
        texto = f'Contador: {self.contador}'  # Texto do contador
        cv2.putText(img, texto, (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)  # Exibe o contador

        cv2.imshow('Resultado', img)  # Mostra o quadro na janela

        # Para a contagem se 'q' for pressionado
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.stop_counting(None)

    # Processa os landmarks detectados
    def process_landmarks(self, results, img):
        h, w, _ = img.shape  # Obtém as dimensões da imagem

        if results.pose_landmarks: # Verifica se landmarks de pose foram detectados

           # Obtém as coordenadas dos landmarks das mãos e pés
           peDY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_FOOT_INDEX].y * h)
           peDX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_FOOT_INDEX].x * w)
           peEY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_FOOT_INDEX].y * h)
           peEX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_FOOT_INDEX].x * w)
           moDY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_INDEX].y * h)
           moDX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.RIGHT_INDEX].x * w)
           moEY = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_INDEX].y * h)
           moEX = int(results.pose_landmarks.landmark[self.pose.PoseLandmark.LEFT_INDEX].x * w)

         # Chama a função para contar os exercícios de polichinelo
        self.count_polichinelo(moDX, moDY, moEX, moEY, peDX, peDY, peEX, peEY)

    def count_polichinelo(self, moDX, moDY, moEX, moEY, peDX, peDY, peEX, peEY):
    # Calcula a distância entre as mãos
        distMO = math.hypot(moDX - moEX, moDY - moEY)
    # Calcula a distância entre os pés
        distPE = math.hypot(peDX - peEX, peDY - peEY)

    # Imprime as distâncias para depuração
        print(f'maos {distMO} pes {distPE}')

    # Define limites de distância para as mãos e pés
        LIMITE_DISTANCIA_MAO = 150
        LIMITE_DISTANCIA_PE = 150

    # Verifica se as distâncias estão dentro dos limites
        if self.check and distMO <= LIMITE_DISTANCIA_MAO and distPE >= LIMITE_DISTANCIA_PE:
        # Incrementa o contador se a condição for satisfeita
           self.contador += 1
           self.check = False  # Reseta a verificação
           self.update_label()  # Atualiza o rótulo com o contador

    # Reseta a verificação se as distâncias não atenderem aos critérios
        if distMO > LIMITE_DISTANCIA_MAO and distPE < LIMITE_DISTANCIA_PE:
           self.check = True

    def update_label(self):
    # Atualiza o texto do rótulo com a contagem atual de exercícios
        self.label.text = f'Contador de Exercícios: {self.contador}'
        if self.sound:
           self.sound.play()  # Reproduz um som, se estiver habilitado

if __name__ == '__main__':
    MainApp().run()  # Executa a aplicação principal
