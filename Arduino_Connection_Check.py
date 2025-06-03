import socket
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import matplotlib
matplotlib.rc('font', family='Malgun Gothic')  # 한글 깨짐 방지

temperature_data = []
humidity_data = []
time_data = []

client_socket = None
connected = False

def connect_to_server():
    global client_socket, connected
    server_ip = ip_entry.get().strip()
    try:
        server_port = int(port_entry.get().strip())
    except ValueError:
        status_label.config(text="포트는 숫자여야 합니다.", foreground="red")
        return

    try:
        client_socket = socket.socket()
        client_socket.connect((server_ip, server_port))
        connected = True
        connect_button.config(state=tk.DISABLED)
        disconnect_button.config(state=tk.NORMAL)
        status_label.config(text="서버에 연결됨", foreground="green")
    except Exception as e:
        status_label.config(text=f"연결 실패: {e}", foreground="red")

def disconnect_from_server():
    global client_socket, connected
    try:
        if client_socket:
            client_socket.close()
        connected = False
        client_socket = None
        connect_button.config(state=tk.NORMAL)
        disconnect_button.config(state=tk.DISABLED)
        status_label.config(text="서버 연결 해제됨", foreground="gray")
    except Exception as e:
        status_label.config(text=f"해제 실패: {e}", foreground="red")

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
    response = send_command(f"LED={int(value)}")
    led_status_label.config(text=f"LED 명령 응답: {response}")

# tkinter GUI 설정
root = tk.Tk()
root.title("아두이노 연결 유지형 클라이언트")

main_frame = ttk.Frame(root, padding=10)
main_frame.pack()

# IP & PORT 입력 필드
ip_frame = ttk.Frame(main_frame)
ip_frame.pack(pady=5)

ttk.Label(ip_frame, text="서버 IP:").pack(side=tk.LEFT)
ip_entry = ttk.Entry(ip_frame, width=15)
ip_entry.insert(0, "113.198.233.228")
ip_entry.pack(side=tk.LEFT, padx=(0, 10))

ttk.Label(ip_frame, text="포트:").pack(side=tk.LEFT)
port_entry = ttk.Entry(ip_frame, width=6)
port_entry.insert(0, "8080")
port_entry.pack(side=tk.LEFT)

# 연결/해제 버튼
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=5)

connect_button = ttk.Button(button_frame, text="서버 연결", command=connect_to_server)
connect_button.pack(side=tk.LEFT, padx=5)

disconnect_button = ttk.Button(button_frame, text="연결 해제", command=disconnect_from_server, state=tk.DISABLED)
disconnect_button.pack(side=tk.LEFT, padx=5)

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
