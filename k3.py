import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

class CorrosionModel:
    """Модель расчёта коррозии трубопровода"""
    
    def __init__(self):
        # Коэффициенты по умолчанию
        self.alpha = 0.035  # температурный коэффициент (1/°C)
        self.beta = 0.02    # коэффициент влияния давления (1/МПа)
        self.K = 1.3        # коэффициент запаса
        
        # Базовые значения
        self.T0 = 20.0      # базовая температура (°C)
        self.P0 = 1.0       # базовое давление (МПа)
        
        # Коэффициенты среды
        self.env_factors = {
            "Нейтральная": 1.0,
            "CO2 (углекислый газ)": 1.75,
            "H2S (сероводород)": 2.5,
            "CO2 + H2S": 3.0,
            "Кислородная коррозия": 2.0,
            "Морская вода": 2.2
        }
    
    def calculate_corrosion_rate(self, S0, Scurrent, texp, T, P, env_factor):
        """Расчёт итоговой скорости коррозии"""
        if texp <= 0:
            return 0
        v_base = (S0 - Scurrent) / texp
        temp_correction = np.exp(self.alpha * (T - self.T0))
        pressure_correction = 1 + self.beta * (P - self.P0)
        v_final = v_base * temp_correction * pressure_correction * env_factor
        return max(v_final, 0.001)
    
    def calculate_remaining_life(self, Scurrent, Smin, v_final):
        """Расчёт остаточного срока службы"""
        if v_final <= 0:
            return float('inf')
        return (Scurrent - Smin) / v_final
    
    def calculate_safe_life(self, Scurrent, Smin, v_final, K):
        """Расчёт безопасного срока с коэффициентом запаса"""
        t_res = self.calculate_remaining_life(Scurrent, Smin, v_final)
        return t_res / K
    
    def predict_thickness_over_time(self, Scurrent, v_final, max_years):
        """Прогноз изменения толщины во времени"""
        time_points = np.linspace(0, max_years, 200)
        thickness = Scurrent - v_final * time_points
        thickness = np.maximum(thickness, 0)
        return time_points, thickness


class CorrosionApp:
    """Главное окно приложения с расширенной визуализацией"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Модель расчёта коррозии трубопровода - Профессиональная визуализация")
        self.root.geometry("1400x850")
        self.root.configure(bg='#f0f0f0')
        
        self.model = CorrosionModel()
        self.current_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Создание интерфейса"""
        # Создаём вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Вкладка расчёта
        self.calc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_frame, text="📊 Расчёт коррозии")
        
        # Вкладка визуализации (расширенная)
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="📈 Расширенная визуализация")
        
        # Вкладка 3D визуализации
        self.viz3d_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz3d_frame, text="🎯 3D Анализ")
        
        # Вкладка справки
        self.help_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.help_frame, text="ℹ️ Справка")
        
        self.setup_calculation_tab()
        self.setup_viz_tab()
        self.setup_viz3d_tab()
        self.setup_help_tab()
        
    def setup_calculation_tab(self):
        """Настройка вкладки расчёта"""
        # Левая панель с вводом данных
        input_frame = tk.Frame(self.calc_frame, bg='#f0f0f0')
        input_frame.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        
        # Правая панель с результатами
        result_frame = tk.Frame(self.calc_frame, bg='#e0e0e0', relief='ridge', bd=2)
        result_frame.pack(side='right', fill='both', expand=True, padx=20, pady=20)
        
        # Заголовок
        title = tk.Label(input_frame, text="Входные параметры", 
                        font=('Arial', 16, 'bold'), bg='#f0f0f0')
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Поля ввода
        row = 1
        fields = [
            ("S0 - Начальная толщина стенки (мм):", "S0", 12.0),
            ("Scurrent - Текущая толщина (мм):", "Scurrent", 8.5),
            ("texp - Время эксплуатации (лет):", "texp", 10.0),
            ("Smin - Минимально допустимая толщина (мм):", "Smin", 5.0),
            ("T - Рабочая температура (°C):", "T", 60.0),
            ("P - Рабочее давление (МПа):", "P", 5.0),
        ]
        
        self.entries = {}
        for label, key, default in fields:
            tk.Label(input_frame, text=label, font=('Arial', 10), 
                    bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
            entry = tk.Entry(input_frame, width=15, font=('Arial', 10))
            entry.insert(0, str(default))
            entry.grid(row=row, column=1, padx=10, pady=5)
            self.entries[key] = entry
            row += 1
        
        # Выбор среды
        tk.Label(input_frame, text="Тип среды:", font=('Arial', 10), 
                bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
        self.env_var = tk.StringVar(value="CO2 (углекислый газ)")
        env_menu = ttk.Combobox(input_frame, textvariable=self.env_var, 
                                 values=list(self.model.env_factors.keys()),
                                 width=25, state='readonly')
        env_menu.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Коэффициенты
        tk.Label(input_frame, text="Дополнительные коэффициенты:", 
                font=('Arial', 12, 'bold'), bg='#f0f0f0')\
                .grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        coefs = [
            ("α - Температурный коэффициент (1/°C):", "alpha", 0.035),
            ("β - Коэффициент давления (1/МПа):", "beta", 0.02),
            ("K - Коэффициент запаса:", "K", 1.3),
        ]
        
        for label, key, default in coefs:
            tk.Label(input_frame, text=label, font=('Arial', 10), 
                    bg='#f0f0f0').grid(row=row, column=0, sticky='w', pady=5)
            entry = tk.Entry(input_frame, width=15, font=('Arial', 10))
            entry.insert(0, str(default))
            entry.grid(row=row, column=1, padx=10, pady=5)
            self.entries[key] = entry
            row += 1
        
        # Кнопка расчёта
        calc_btn = tk.Button(input_frame, text="РАССЧИТАТЬ", 
                            font=('Arial', 12, 'bold'), bg='#4CAF50', 
                            fg='white', command=self.calculate)
        calc_btn.grid(row=row, column=0, columnspan=2, pady=20)
        
        # Результаты
        result_title = tk.Label(result_frame, text="Результаты расчёта", 
                               font=('Arial', 16, 'bold'), bg='#e0e0e0')
        result_title.pack(pady=10)
        
        # Создаём фрейм для результата с прокруткой
        result_text_frame = tk.Frame(result_frame)
        result_text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(result_text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.result_text = tk.Text(result_text_frame, width=45, height=22, 
                                   font=('Courier', 9), bg='white',
                                   yscrollcommand=scrollbar.set)
        self.result_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.result_text.yview)
        
    def setup_viz_tab(self):
        """Настройка вкладки расширенной визуализации (6 графиков)"""
        # Создаём фигуру с 6 подграфиками
        self.figure_viz = Figure(figsize=(14, 10))
        
        # График 1: Изменение толщины
        self.ax1 = self.figure_viz.add_subplot(2, 3, 1)
        
        # График 2: Скорость коррозии по факторам
        self.ax2 = self.figure_viz.add_subplot(2, 3, 2)
        
        # График 3: Запас прочности
        self.ax3 = self.figure_viz.add_subplot(2, 3, 3)
        
        # График 4: Температурная зависимость
        self.ax4 = self.figure_viz.add_subplot(2, 3, 4)
        
        # График 5: Влияние среды
        self.ax5 = self.figure_viz.add_subplot(2, 3, 5)
        
        # График 6: Круговая диаграмма ресурса
        self.ax6 = self.figure_viz.add_subplot(2, 3, 6)
        
        self.figure_viz.suptitle("Комплексный анализ коррозионного состояния трубопровода", 
                                 fontsize=14, fontweight='bold')
        
        self.figure_viz.tight_layout(pad=3.0)
        
        self.canvas_viz = FigureCanvasTkAgg(self.figure_viz, self.viz_frame)
        self.canvas_viz.get_tk_widget().pack(fill='both', expand=True)
        
        # Кнопка обновления
        update_btn = tk.Button(self.viz_frame, text="Обновить визуализацию", 
                              command=self.update_visualization, 
                              bg='#2196F3', fg='white', 
                              font=('Arial', 10, 'bold'), height=2)
        update_btn.pack(pady=5)
        
        # Информационная строка
        info_label = tk.Label(self.viz_frame, 
                             text="💡 Наведённые графики показывают все аспекты коррозионного процесса",
                             font=('Arial', 9), fg='gray')
        info_label.pack(pady=2)
        
    def setup_viz3d_tab(self):
        """Настройка вкладки 3D визуализации"""
        # Создаём фигуру для 3D
        self.figure_3d = Figure(figsize=(12, 8))
        self.ax_3d = self.figure_3d.add_subplot(111, projection='3d')
        
        self.canvas_3d = FigureCanvasTkAgg(self.figure_3d, self.viz3d_frame)
        self.canvas_3d.get_tk_widget().pack(fill='both', expand=True)
        
        # Кнопка обновления 3D
        update_btn_3d = tk.Button(self.viz3d_frame, text="Обновить 3D визуализацию", 
                                  command=self.update_3d_visualization,
                                  bg='#9C27B0', fg='white', 
                                  font=('Arial', 10, 'bold'), height=2)
        update_btn_3d.pack(pady=5)
        
    def setup_help_tab(self):
        """Настройка вкладки справки"""
        help_text = tk.Text(self.help_frame, font=('Arial', 10), wrap='word')
        help_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        info = """
        📚 МОДЕЛЬ РАСЧЁТА КОРРОЗИИ ТРУБОПРОВОДА
        =========================================
        
        🎯 РАСШИРЕННАЯ ВИЗУАЛИЗАЦИЯ ВКЛЮЧАЕТ:
        
        1️⃣ График изменения толщины стенки во времени
           - Показывает прогноз до полного износа
           - Зоны безопасности и опасности
        
        2️⃣ Диаграмма вклада факторов в коррозию
           - Температурный вклад
           - Давление
           - Химическая среда
        
        3️⃣ Запас прочности
           - Текущий запас в процентах
           - Цветовая индикация состояния
        
        4️⃣ Температурная зависимость
           - Скорость коррозии от температуры
           - Оптимальный диапазон
        
        5️⃣ Влияние типа среды
           - Сравнение всех типов сред
           - Рекомендации по выбору
        
        6️⃣ Распределение ресурса
           - Круговая диаграмма срока службы
        
        🎨 3D ВИЗУАЛИЗАЦИЯ:
        
        • 3D поверхность коррозии
        • Влияние температуры и времени
        • Интерактивное вращение
        
        📊 ФОРМУЛЫ ВИЗУАЛИЗАЦИИ:
        
        • Толщина: h(t) = Scurrent - v*t
        • Скорость: v(T) = v0 * e^(α*(T-T0))
        • Запас: Margin = (Scurrent - Smin)/(S0 - Smin) * 100%
        
        🎮 УПРАВЛЕНИЕ:
        
        • 3D график можно вращать мышью
        • Используйте обновление для перерисовки
        • Все графики обновляются автоматически
        """
        
        help_text.insert('1.0', info)
        help_text.config(state='disabled')
        
    def calculate(self):
        """Выполнение расчёта"""
        try:
            # Получение данных
            S0 = float(self.entries['S0'].get())
            Scurrent = float(self.entries['Scurrent'].get())
            texp = float(self.entries['texp'].get())
            Smin = float(self.entries['Smin'].get())
            T = float(self.entries['T'].get())
            P = float(self.entries['P'].get())
            
            # Коэффициенты
            self.model.alpha = float(self.entries['alpha'].get())
            self.model.beta = float(self.entries['beta'].get())
            K = float(self.entries['K'].get())
            
            # Коэффициент среды
            env_name = self.env_var.get()
            k_env = self.model.env_factors[env_name]
            
            # Проверки
            if texp <= 0:
                messagebox.showerror("Ошибка", "Время эксплуатации должно быть > 0")
                return
            if Scurrent >= S0:
                messagebox.showerror("Ошибка", "Текущая толщина не может быть больше начальной")
                return
            if Scurrent <= Smin:
                messagebox.showerror("Ошибка", "Текущая толщина уже меньше минимально допустимой!")
                return
            
            # Расчёты
            v_base = (S0 - Scurrent) / texp
            v_temp = v_base * np.exp(self.model.alpha * (T - self.model.T0))
            v_pressure = v_temp * (1 + self.model.beta * (P - self.model.P0))
            v_final = v_pressure * k_env
            
            t_res = (Scurrent - Smin) / v_final
            t_safe = t_res / K
            
            # Сохраняем данные для визуализации
            self.current_data = {
                'S0': S0, 'Scurrent': Scurrent, 'Smin': Smin,
                'texp': texp, 'T': T, 'P': P,
                'v_base': v_base, 'v_temp': v_temp, 'v_pressure': v_pressure,
                'v_final': v_final, 't_res': t_res, 't_safe': t_safe,
                'k_env': k_env, 'env_name': env_name, 'K': K
            }
            
            # Формирование отчёта
            report = f"""
╔══════════════════════════════════════════════════════════╗
║                  РЕЗУЛЬТАТЫ РАСЧЁТА                      ║
╚══════════════════════════════════════════════════════════╝

📐 ИСХОДНЫЕ ДАННЫЕ:
───────────────────────────────────────────────────────────
  Начальная толщина (S0):           {S0:.2f} мм
  Текущая толщина (Scurrent):       {Scurrent:.2f} мм
  Минимальная толщина (Smin):       {Smin:.2f} мм
  Время эксплуатации (texp):        {texp:.1f} лет

🌡️ ЭКСПЛУАТАЦИОННЫЕ ФАКТОРЫ:
───────────────────────────────────────────────────────────
  Рабочая температура (T):          {T:.1f} °C
  Рабочее давление (P):             {P:.1f} МПа
  Тип среды:                        {env_name}
  Коэффициент среды (k_env):        {k_env:.2f}

⚙️ КОЭФФИЦИЕНТЫ МОДЕЛИ:
───────────────────────────────────────────────────────────
  Температурный (α):                {self.model.alpha:.3f} 1/°C
  Давления (β):                     {self.model.beta:.3f} 1/МПа
  Запаса (K):                       {K:.2f}

📊 РАСЧЁТНЫЕ ПОКАЗАТЕЛИ:
───────────────────────────────────────────────────────────
  Базовая скорость коррозии:        {v_base:.4f} мм/год
  С учётом температуры:             {v_temp:.4f} мм/год
  С учётом давления:                {v_pressure:.4f} мм/год
  Итоговая скорость (v_final):      {v_final:.4f} мм/год

🎯 ГЛАВНЫЙ РЕЗУЛЬТАТ:
───────────────────────────────────────────────────────────
  Остаточный срок службы (t_res):   {t_res:.1f} лет
  ✅ БЕЗОПАСНЫЙ СРОК (t_safe):       {t_safe:.1f} лет

⚠️ РЕКОМЕНДАЦИИ:
───────────────────────────────────────────────────────────
"""
            
            if t_safe > 20:
                report += "  ✅ Отличное состояние! Регулярный мониторинг раз в 5 лет."
            elif t_safe > 10:
                report += "  ✅ Хорошее состояние. Мониторинг раз в 3 года."
            elif t_safe > 5:
                report += "  ⚠️ Удовлетворительное. Мониторинг раз в год."
            elif t_safe > 2:
                report += "  ⚠️ Требуется внимание! Плановый ремонт в течение 2 лет."
            else:
                report += "  ❌ КРИТИЧНО! Срочная замена трубопровода!"
            
            self.result_text.delete('1.0', tk.END)
            self.result_text.insert('1.0', report)
            
            # Обновляем визуализацию
            self.update_visualization()
            self.update_3d_visualization()
            
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", f"Пожалуйста, проверьте правильность ввода чисел.\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
    
    def update_visualization(self):
        """Обновление всех 6 графиков визуализации"""
        if not self.current_data:
            messagebox.showwarning("Предупреждение", "Сначала выполните расчёт!")
            return
        
        data = self.current_data
        
        # График 1: Изменение толщины стенки во времени
        self.ax1.clear()
        years = np.linspace(0, data['t_safe'] * 2, 200)
        thickness = data['Scurrent'] - data['v_final'] * years
        thickness = np.maximum(thickness, 0)
        
        self.ax1.plot(years, thickness, 'b-', linewidth=2.5, label='Толщина стенки')
        self.ax1.axhline(y=data['Smin'], color='r', linestyle='--', 
                        linewidth=2, label=f'Минимум ({data["Smin"]} мм)')
        self.ax1.axvline(x=data['t_safe'], color='g', linestyle='-.', 
                        linewidth=2, label=f'Безопасный срок ({data["t_safe"]:.1f} лет)')
        self.ax1.fill_between(years, 0, thickness, where=(thickness >= data['Smin']), 
                              color='green', alpha=0.2)
        self.ax1.fill_between(years, 0, thickness, where=(thickness < data['Smin']), 
                              color='red', alpha=0.3)
        self.ax1.set_xlabel('Время (годы)', fontsize=10)
        self.ax1.set_ylabel('Толщина стенки (мм)', fontsize=10)
        self.ax1.set_title('📉 Прогноз износа стенки', fontsize=11, fontweight='bold')
        self.ax1.legend(loc='upper right', fontsize=8)
        self.ax1.grid(True, alpha=0.3)
        
        # График 2: Вклад факторов в коррозию
        self.ax2.clear()
        factors = ['Базовая\nскорость', 'Температура', 'Давление', 'Среда']
        values = [data['v_base'], data['v_temp'] - data['v_base'],
                 data['v_pressure'] - data['v_temp'], 
                 data['v_final'] - data['v_pressure']]
        colors = ['#3498db', '#e74c3c', '#f39c12', '#9b59b6']
        bars = self.ax2.bar(factors, values, color=colors, alpha=0.7, edgecolor='black')
        self.ax2.set_ylabel('Увеличение скорости (мм/год)', fontsize=10)
        self.ax2.set_title('📊 Вклад факторов в коррозию', fontsize=11, fontweight='bold')
        self.ax2.grid(True, alpha=0.3, axis='y')
        
        # Добавление значений на столбцы
        for bar, val in zip(bars, values):
            if val > 0:
                self.ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.0005,
                             f'{val:.4f}', ha='center', va='bottom', fontsize=8, rotation=0)
        
        # График 3: Запас прочности
        self.ax3.clear()
        total_loss = data['S0'] - data['Smin']
        current_loss = data['S0'] - data['Scurrent']
        safety_margin = (data['Scurrent'] - data['Smin']) / (data['S0'] - data['Smin']) * 100
        
        # Создаём круговую диаграмму запаса
        remaining = max(0, safety_margin)
        used = 100 - remaining
        
        wedges, texts, autotexts = self.ax3.pie([remaining, used], 
                                                  labels=[f'Остаток\n{remaining:.1f}%', 
                                                          f'Износ\n{used:.1f}%'],
                                                  colors=['#2ecc71', '#e74c3c'],
                                                  autopct='%1.1f%%', startangle=90,
                                                  explode=(0.05, 0))
        self.ax3.set_title('🛡️ Запас прочности', fontsize=11, fontweight='bold')
        
        # Добавляем центр
        centre_circle = plt.Circle((0, 0), 0.70, fc='white', linewidth=1.5, edgecolor='black')
        self.ax3.add_artist(centre_circle)
        self.ax3.text(0, 0, f'{remaining:.0f}%', ha='center', va='center', fontsize=14, fontweight='bold')
        
        # График 4: Температурная зависимость
        self.ax4.clear()
        temp_range = np.linspace(0, 100, 100)
        v_temp_effect = data['v_base'] * np.exp(self.model.alpha * (temp_range - self.model.T0))
        
        self.ax4.plot(temp_range, v_temp_effect, 'r-', linewidth=2.5, label='Скорость коррозии')
        self.ax4.axvline(x=data['T'], color='b', linestyle='--', linewidth=2, 
                        label=f'Рабочая T = {data["T"]}°C')
        self.ax4.fill_between(temp_range, data['v_base'], v_temp_effect, 
                              where=(v_temp_effect > data['v_base']), color='red', alpha=0.2)
        self.ax4.set_xlabel('Температура (°C)', fontsize=10)
        self.ax4.set_ylabel('Скорость коррозии (мм/год)', fontsize=10)
        self.ax4.set_title('🌡️ Температурная зависимость', fontsize=11, fontweight='bold')
        self.ax4.legend(fontsize=8)
        self.ax4.grid(True, alpha=0.3)
        
        # График 5: Влияние различных сред
        self.ax5.clear()
        env_names = list(self.model.env_factors.keys())
        env_values = list(self.model.env_factors.values())
        env_rates = [data['v_pressure'] * val for val in env_values]
        
        bars = self.ax5.barh(env_names, env_rates, color='skyblue', edgecolor='navy', alpha=0.7)
        
        # Выделяем текущую среду
        current_idx = env_names.index(data['env_name'])
        bars[current_idx].set_color('orange')
        bars[current_idx].set_edgecolor('red')
        bars[current_idx].set_linewidth(2)
        
        self.ax5.set_xlabel('Скорость коррозии (мм/год)', fontsize=10)
        self.ax5.set_title('🌊 Влияние химической среды', fontsize=11, fontweight='bold')
        self.ax5.grid(True, alpha=0.3, axis='x')
        
        # График 6: Распределение ресурса
        self.ax6.clear()
        resources = ['Использованный\nресурс', 'Остаточный\nресурс', 'Запас\nпрочности']
        used_resource = data['texp']
        remaining_resource = data['t_res']
        safety_resource = data['t_safe'] - remaining_resource if data['t_safe'] > remaining_resource else 0
        
        values_res = [used_resource, remaining_resource, safety_resource]
        colors_res = ['#95a5a6', '#3498db', '#2ecc71']
        explode_res = (0, 0.05, 0)
        
        wedges, texts, autotexts = self.ax6.pie(values_res, labels=resources, colors=colors_res,
                                                  autopct='%1.1f%%', startangle=90, explode=explode_res)
        self.ax6.set_title('⏰ Распределение срока службы', fontsize=11, fontweight='bold')
        
        self.figure_viz.tight_layout(pad=3.0)
        self.canvas_viz.draw()
    
    def update_3d_visualization(self):
        """Обновление 3D визуализации"""
        if not self.current_data:
            messagebox.showwarning("Предупреждение", "Сначала выполните расчёт!")
            return
        
        data = self.current_data
        
        self.ax_3d.clear()
        
        # Создаём сетку для 3D поверхности
        X = np.linspace(0, data['t_safe'] * 1.5, 50)
        Y = np.linspace(0, 100, 50)
        X, Y = np.meshgrid(X, Y)
        
        # Расчёт Z (скорость коррозии от времени и температуры)
        Z = data['v_base'] * np.exp(self.model.alpha * (Y - self.model.T0))
        Z = Z * (1 + 0.1 * np.sin(X / 5))  # Добавляем вариативность
        
        # Построение поверхности
        surf = self.ax_3d.plot_surface(X, Y, Z, cmap='hot', alpha=0.8, linewidth=0, antialiased=True)
        
        # Настройка осей
        self.ax_3d.set_xlabel('Время (годы)', fontsize=10, labelpad=10)
        self.ax_3d.set_ylabel('Температура (°C)', fontsize=10, labelpad=10)
        self.ax_3d.set_zlabel('Скорость коррозии\n(мм/год)', fontsize=10, labelpad=10)
        self.ax_3d.set_title('🎯 3D Поверхность коррозии\n(влияние времени и температуры)', 
                             fontsize=12, fontweight='bold')
        
        # Добавляем цветовую шкалу
        self.figure_3d.colorbar(surf, ax=self.ax_3d, shrink=0.5, aspect=10, label='Скорость коррозии (мм/год)')
        
        # Отмечаем рабочую точку
        self.ax_3d.scatter([data['texp']], [data['T']], [data['v_final']], 
                          color='red', s=100, label='Рабочая точка', edgecolor='white', linewidth=2)
        
        self.ax_3d.legend(loc='upper left')
        
        self.canvas_3d.draw()


def main():
    root = tk.Tk()
    app = CorrosionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
