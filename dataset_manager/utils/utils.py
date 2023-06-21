#!/usr/bin/python3
import cv2
import mediapipe as mp
import os

"""
The Utils class provides utility functions for hand detection and annotation. It includes methods for configuring and detecting hands using the MediaPipe Hands model, converting hand positions to YOLO format, annotating images with bounding boxes, and saving resized hand images to disk. The class also includes methods for tracking hand positions and drawing bounding boxes around hands in images.

Methods:
- Hands_model_configuration: Configures the MediaPipe Hands model with specified parameters.
- Hands_detection: Detects hands in an image using the MediaPipe Hands model.
- convert_to_yolo_format: Converts hand positions to YOLO format.
- anotation_data: Annotates an image with bounding boxes around detected hands and saves the annotation data to a file.
- Detect_hand_type: Tracks the position of a specified hand type in an image.
- get_position: Gets the position of a hand in an image.
- Draw_Bound_Boxes: Draws a bounding box around a hand in an image.
- Get_image_resized: Resizes an image to focus on a detected hand.
- Save_resized_hand: Saves a resized hand image to disk.

Fields:
- DATA_PATH: The path to the directory where hand images will be saved.
- actions: A list of actions to be performed by the user.
- imgSize: The size to which hand images will be resized.
- size_data: The total number of hand images to be captured.
- save_frequency: The frequency at which hand images will be saved.
- offset: The offset used when drawing bounding boxes around hands in images.
"""


mp_hands = mp.solutions.hands


class Utils:
    def __init__(self, DATA_PATH=None, actions=None, imgSize=None, size_data=None):
        self.DATA_PATH = DATA_PATH
        self.actions = actions
        self.imgSize = imgSize
        self.size_data = size_data
        self.save_frequency = 10
        self.offset = 10

        if actions is not None:
            for action in self.actions:
                try:
                    os.makedirs(os.path.join(self.DATA_PATH, action))
                except:
                    pass

    @staticmethod
    def Hands_model_configuration(image_mode, max_hand, complexity):
        hands = mp_hands.Hands(
            static_image_mode=image_mode,
            max_num_hands=max_hand,
            model_complexity=complexity,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        return hands

    @staticmethod
    def Hands_detection(image, model):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        result = model.process(image)
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image, result

    @staticmethod
    def convert_to_yolo_format(image_width, image_height, key_points):
        x_center = (key_points[0] + key_points[2]) / 2 / image_width
        y_center = (key_points[1] + key_points[3]) / 2 / image_height
        width = abs(key_points[2] - key_points[0]) / image_width
        height = abs(key_points[3] - key_points[1]) / image_height

        return f"{x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"

    # @staticmethod
    # def anotation_data(results, image, annotation_file, class_index):
    #     with open(annotation_file, 'a') as f:
    #         for hand_landmarks in results.multi_hand_landmarks:
    #             keypoints = []
    #             for id, lm in enumerate(hand_landmarks.landmark):
    #                 alto, ancho, c = image.shape
    #                 x_rel = lm.x * ancho
    #                 y_rel = lm.y * alto
    #                 keypoints.extend([x_rel, y_rel])
    #
    #             x_min = min(keypoints[0::2])
    #             y_min = min(keypoints[1::2])
    #             x_max = max(keypoints[0::2])
    #             y_max = max(keypoints[1::2])
    #
    #             x_min -= 20
    #             y_min -= 20
    #             x_max += 20
    #             y_max += 20
    #
    #             annotation_data = f"{class_index} {Utils.convert_to_yolo_format(ancho, alto, [x_min, y_min, x_max, y_max])}"
    #             f.write(annotation_data + '\n')

    @staticmethod
    def anotation_data(results, image, annotation_file, class_index):
        with open(annotation_file, 'a') as f:
            x_min = float('inf')
            y_min = float('inf')
            x_max = float('-inf')
            y_max = float('-inf')

            for hand_landmarks in results.multi_hand_landmarks:
                keypoints = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    alto, ancho, c = image.shape
                    x_rel = lm.x * ancho
                    y_rel = lm.y * alto
                    keypoints.extend([x_rel, y_rel])

                hand_x_min = min(keypoints[0::2])
                hand_y_min = min(keypoints[1::2])
                hand_x_max = max(keypoints[0::2])
                hand_y_max = max(keypoints[1::2])

                x_min = min(x_min, hand_x_min)
                y_min = min(y_min, hand_y_min)
                x_max = max(x_max, hand_x_max)
                y_max = max(y_max, hand_y_max)

            x_min -= 20
            y_min -= 20
            x_max += 20
            y_max += 20

            annotation_data = f"{class_index} {Utils.convert_to_yolo_format(ancho, alto, [x_min, y_min, x_max, y_max])}"
            f.write(annotation_data + '\n')

    @staticmethod
    def Detect_hand_type(hand_type, results, positions, copie_img):
        """
        tracking of the position of the hand in the image, depending on the image chosen by the user

        hand_type: Left or Right hand type
        results: detection results
        positions: list of positions
        copie_img: copy image

        return: position of the hand
        """
        for hand_index, hand_info in enumerate(results.multi_handedness):
            hand_types = hand_info.classification[0].label
            if hand_types == hand_type:
                Utils.get_position(positions, results, copie_img)
            if hand_type == "all":
                Utils.get_position(positions, results, copie_img)
            return positions

    @staticmethod
    def get_position(positions, results, copie_img):
        for hand_landmarks in results.multi_hand_landmarks:
            for id, lm in enumerate(hand_landmarks.landmark):
                alto, ancho, c = copie_img.shape
                positions.append((lm.x * ancho, lm.y * alto, lm.z * ancho))


    def Draw_Bound_Boxes(self, positions, frame, cls=""):
        """
        hand box

        :param positions: Position array
        :param frame: Frame
        """
        x_min = int(min(positions, key=lambda x: x[0])[0])
        y_min = int(min(positions, key=lambda x: x[1])[1])
        x_max = int(max(positions, key=lambda x: x[0])[0])
        y_max = int(max(positions, key=lambda x: x[1])[1])
        width = x_max - x_min
        height = y_max - y_min
        x1, y1 = x_min, y_min
        x2, y2 = x_min + width, y_min + height
        if y1 - self.offset - 15 >= 0 and y2 - self.offset + 40 <= frame.shape[
            0] and x1 - self.offset - 40 >= 0 and x2 - self.offset + 50 <= \
                frame.shape[1]:
            cv2.rectangle(frame, (x1 - self.offset - 40, y1 - self.offset - 15), (x2 - self.offset + 50, y2 - self.offset + 40),
                          (0, 255, 0), 3)
            cv2.putText(frame, f'{cls}' , (x1 - self.offset - 40, y1 - self.offset - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.60, [225, 255, 255], thickness=1)

    def Get_image_resized(self, positions, copie_img):
        """
        image reshaping

        :param positions: x y z coordinates
        :param copie_img: copy frame

        return: redeemed image
        """
        alto, ancho, c = copie_img.shape
        x_min = int(min(positions, key=lambda x: x[0])[0])
        y_min = int(min(positions, key=lambda x: x[1])[1])
        x_max = int(max(positions, key=lambda x: x[0])[0])
        y_max = int(max(positions, key=lambda x: x[1])[1])
        width = x_max - x_min
        height = y_max - y_min
        centro_x, centro_y = int((x_min + x_max) / 2), int((y_min + y_max) / 2)
        # Calcular las coordenadas del cuadro centrado en la mano
        lado = max(width, height)
        x1 = max(0, centro_x - int(lado / 2) - 50)
        y1 = max(0, centro_y - int(lado / 2) - 50)
        ancho = min(ancho - x1, int(lado) + 100)
        alto = min(alto - y1, int(lado) + 100)
        x2, y2 = x1 + ancho, y1 + alto
        resized_hand = copie_img[y1:y2, x1:x2]
        resized_hand = cv2.resize(resized_hand, (self.imgSize, self.imgSize), interpolation=cv2.INTER_CUBIC)
        cv2.imshow("resized_hand", resized_hand)
        return resized_hand

    def Save_resized_hand(self, resized_hand, count, hand_type):
        """
        Guarda la imagen capturada

        :param resized_hand: imagen
        :param count: contador
        :param hand_type: Izquierda o Derecha
        """
        for action in self.actions:
            for sequence in range(self.save_frequency):
                image_name = f'sequence {sequence} capture {hand_type} {count}.png'
                image_path = os.path.join(self.DATA_PATH, action, image_name)

                # Verificar si el archivo ya existe
                if os.path.exists(image_path):
                    # Generar un nuevo nombre de archivo único
                    index = 1
                    while True:
                        new_image_name = f'sequence {sequence} capture {hand_type} {count}_{index}.png'
                        new_image_path = os.path.join(self.DATA_PATH, action, new_image_name)
                        if not os.path.exists(new_image_path):
                            image_path = new_image_path
                            break
                        index += 1
                cv2.imwrite(image_path, resized_hand)
        if count >= self.size_data / self.save_frequency:
            exit(0)