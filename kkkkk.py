import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

# ========== 1. Параметры трубопровода ==========
initial_thickness = 12.0   # мм
corrosion_rate = 0.15      # мм/год
min_required_thickness = 5.0  # мм
length = 1000              # м (длина трубы для "горячих точек")

years = np.linspace(0, 50, 200)
thickness = initial_thickness - corrosion_rate * years
thickness = np.maximum(thickness, 0)  # не уходит в отрицательные

# ========== 2. Остаточный ресурс ==========
remaining_life = (initial_thickness - min_required_thickness) / corrosion_rate

# ========== 3. Неравномерная коррозия по длине трубы ==========
x_pos = np.linspace(0, length, 100)
# Имитация локальных дефектов (коррозионные язвы)
local_corrosion = corrosion_rate + 0.2 * np.exp(-((x_pos - 400)**2) / (2*100**2)) \
                  + 0.15 * np.exp(-((x_pos - 750)**2) / (2*80**2))
local_thickness = initial_thickness - local_corrosion * 25  # через 25 лет

# ========== 4. ВИЗУАЛИЗАЦИЯ ==========
fig, axes = plt.subplots(2, 2, figsize=(13, 8))
fig.suptitle("Мониторинг и расчёт коррозии трубопровода", fontsize=14, weight='bold')

# График 1: Уменьшение толщины стенки во времени
ax1 = axes[0, 0]
ax1.plot(years, thickness, lw=2, color='darkred')
ax1.axhline(min_required_thickness, color='orange', ls='--', label=f"Min required ({min_required_thickness} мм)")
ax1.axvline(remaining_life, color='green', ls='-.', label=f"Остаточный ресурс: {remaining_life:.1f} лет")
ax1.fill_between(years, 0, thickness, where=(thickness >= min_required_thickness), color='lightgreen', alpha=0.3)
ax1.fill_between(years, 0, thickness, where=(thickness < min_required_thickness), color='salmon', alpha=0.5)
ax1.set_xlabel("Время (годы)")
ax1.set_ylabel("Толщина стенки (мм)")
ax1.set_title("Износ стенки во времени")
ax1.legend()
ax1.grid(alpha=0.3)

# График 2: Скорость коррозии по длине трубопровода (через 25 лет)
ax2 = axes[0, 1]
ax2.plot(x_pos, local_corrosion, 'o-', color='purple', markersize=3)
ax2.fill_between(x_pos, 0, local_corrosion, alpha=0.2, color='violet')
ax2.set_xlabel("Позиция по длине (м)")
ax2.set_ylabel("Скорость коррозии (мм/год)")
ax2.set_title("Локальные ускорения коррозии (дефекты)")
ax2.grid(alpha=0.3)

# График 3: Толщина стенки по длине через заданное время (25 лет)
ax3 = axes[1, 0]
ax3.plot(x_pos, local_thickness, color='navy', lw=2)
ax3.axhline(min_required_thickness, color='red', ls='--', linewidth=1.5)
ax3.fill_between(x_pos, min_required_thickness, local_thickness, 
                  where=(local_thickness < min_required_thickness), color='red', alpha=0.4, label="Опасная зона")
ax3.set_xlabel("Позиция по длине (м)")
ax3.set_ylabel("Толщина стенки (мм)")
ax3.set_title("Профиль толщины стенки через 25 лет эксплуатации")
ax3.legend()
ax3.grid(alpha=0.3)

# График 4: Динамическая карта коррозионных потерь (время × длина)
ax4 = axes[1, 1]
time_grid = np.linspace(0, 30, 50)
pos_grid = np.linspace(0, length, 80)
T, X = np.meshgrid(time_grid, pos_grid)
# Создаём поле коррозии: базовая скорость + локальные пики
base = corrosion_rate
local_effect = 0.25 * np.exp(-((X - 400)**2) / (2*100**2)) + 0.2 * np.exp(-((X - 750)**2) / (2*80**2))
# Исправлено: теперь loss имеет правильную размерность 2D
loss = base * T + local_effect * T

c = ax4.contourf(T, X, loss, levels=20, cmap='hot')
plt.colorbar(c, ax=ax4, label="Потеря толщины (мм)")
ax4.set_xlabel("Время (годы)")
ax4.set_ylabel("Позиция по длине (м)")
ax4.set_title("Тепловая карта коррозионных потерь")
ax4.invert_yaxis()

plt.tight_layout()
plt.show()

# ========== 5. Вывод расчётных параметров ==========
print("=" * 50)
print("РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ КОРРОЗИИ")
print("=" * 50)
print(f"Начальная толщина стенки:       {initial_thickness} мм")
print(f"Средняя скорость коррозии:       {corrosion_rate} мм/год")
print(f"Минимально допустимая толщина:   {min_required_thickness} мм")
print(f"Остаточный ресурс (средний):     {remaining_life:.1f} лет")
print(f"Максимальная локальная скорость: {np.max(local_corrosion):.2f} мм/год (на позиции ~400-750 м)")
print("Рекомендация: Проверить участки 350–450 м и 700–800 м на предмет язвенной коррозии.")
