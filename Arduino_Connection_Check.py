import socket
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import matplotlib
matplotlib.rc('font', family='Malgun Gothic')  # 한글 깨짐 방지

SERVER_IP = "113.198.233.228"
PORT = 8080

temperature_data = []
humidity_data = []
time_data = []

client_socket = None
connected = False

def connect_to_server():
    global client_socket, connected
    try:
        client_socket = socket.socket()
        client_socket.connect((SERVER_IP, PORT))
        connected = True
        connect_button.config(state=tk.DISABLED)
        status_label.config(text="서버에 연결됨", foreground="green")
    except Exception as e:
        status_label.config(text=f"연결 실패: {e}", foreground="red")

def send_command(command):
    global client_socket, connected
    if not connected:
        return "NOT_CONNECTED"
    try:
        client_socket.sendall((command + "\n").encode())
        response = client_socket.recv(1024).decode().strip()
        return response
    except Exception as e:
        return f"ERROR: {e}"

def parse_and_update_data():
    global time_data, temperature_data, humidity_data

    if not connected:
        return

    response = send_command("GET_TEMP")
    if response.startswith("TEMP="):
        try:
            parts = response.replace("TEMP=", "").replace("HUM=", "").split(",")
            temp = float(parts[0])
            hum = float(parts[1])
            ts = time.strftime("%H:%M:%S")

            temperature_data.append(temp)
            humidity_data.append(hum)
            time_data.append(ts)

            if len(time_data) > 20:
                time_data = time_data[-20:]
                temperature_data = temperature_data[-20:]
                humidity_data = humidity_data[-20:]

            temp_label.config(text=f"온도: {temp:.2f} ℃")
            hum_label.config(text=f"습도: {hum:.2f} %")
            update_graph()
        except:
            pass
    else:
        temp_label.config(text="서버 응답 오류")
        hum_label.config(text=response)

def update_graph():
    ax.clear()
    ax.plot(time_data, temperature_data, label="온도 (℃)", marker="o")
    ax.plot(time_data, humidity_data, label="습도 (%)", marker="x")
    ax.set_xticks(range(len(time_data)))
    ax.set_xticklabels(time_data, rotation=45)
    ax.set_title("실시간 온습도 그래프")
    ax.legend(loc="upper left")
    canvas.draw()

def periodic_update():
    while True:
        parse_and_update_data()
        time.sleep(1)

def send_led_command():
    value = led_slider.get()
    response = send_command(f"LED={value}")
    led_status_label.config(text=f"LED 명령 응답: {response}")

# tkinter GUI 설정
root = tk.Tk()
root.title("아두이노 연결 유지형 클라이언트")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack()

connect_button = ttk.Button(main_frame, text="서버 연결", command=connect_to_server)
connect_button.pack(pady=5)

status_label = ttk.Label(main_frame, text="서버에 연결되지 않음", foreground="red")
status_label.pack()

temp_label = ttk.Label(main_frame, text="온도: - ℃", font=("Arial", 16))
temp_label.pack(pady=5)

hum_label = ttk.Label(main_frame, text="습도: - %", font=("Arial", 16))
hum_label.pack(pady=5)

# 그래프
fig = Figure(figsize=(6, 4))
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# LED 제어 UI
led_frame = ttk.Frame(root)
led_frame.pack(pady=10)

ttk.Label(led_frame, text="LED 제어 (0~15):").pack()
led_slider = ttk.Scale(led_frame, from_=0, to=15, orient=tk.HORIZONTAL)
led_slider.pack()

ttk.Button(led_frame, text="LED 설정", command=send_led_command).pack(pady=5)
led_status_label = ttk.Label(led_frame, text="LED 명령 응답: -")
led_status_label.pack()

# 실시간 데이터 스레드
threading.Thread(target=periodic_update, daemon=True).start()
root.mainloop()
