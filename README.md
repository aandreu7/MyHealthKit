## 🤖 Autonomous Medical Robot for Pharmaceutical Support 💊

This project presents the development of an autonomous medical robot designed to optimize the management and dispensing of pharmaceuticals within healthcare environments. The system, based on a Raspberry Pi 4 platform, aims to provide efficient and on-demand support to medical professionals, facilitating access to necessary medication at the point of patient care.

The robot's functionality is structured around the following key capabilities:

* **🗃️ Drug Storage and Dispensing:** The robot integrates a secure storage system and a precise dispensing mechanism, enabling the controlled delivery of medications according to the needs of medical personnel.
* **🗺️ Autonomous Navigation:** Through the implementation of a **SLAM (Simultaneous Localization and Mapping)** system, the robot is capable of mapping its operational environment and navigating autonomously within it. This functionality is activated by scanning QR codes located in different rooms, allowing the user to request the robot's presence at a specific location.
* **📱 Intuitive User Interface:** The robot's control is managed through a mobile application developed using TypeScript, React Native, and Expo. This interface allows users to:
    * 📍 **Request the robot's presence** by scanning QR codes.
    * 🗣️ **Request medications** via voice commands or direct selection within the application.
    * 🤒 **Communicate symptoms** through voice input, enabling the robot to provide medication recommendations based on a preliminary analysis.
* **📦 Inventory Management:** The controller software includes functionalities for managing the inventory of drugs stored within the robot, ensuring accurate stock control and facilitating replenishment.
* **🔁 Bidirectional Communication:** The system enables seamless communication between the user and the robot, both for medication requests and for the transmission of relevant information for dispensing or recommendation purposes.

The repository associated with this project hosts the complete software architecture, divided into two main components:

* **📲 Mobile Application:** Developed with TypeScript, React Native, and Expo, this application provides the graphical interface and interaction logic with the user, enabling remote control of the robot and management of requests.
* **🧠 Controller Software:** This component, executed on the Raspberry Pi 4, implements the SLAM algorithm for autonomous navigation, manages communication with the user via voice and the application, and controls the drug storage and dispensing system, including inventory management.

In summary, this project represents an innovative solution for optimizing pharmaceutical logistics in medical settings, offering an autonomous, remotely controlled system capable of responding to the medication demands of healthcare professionals efficiently and promptly.
