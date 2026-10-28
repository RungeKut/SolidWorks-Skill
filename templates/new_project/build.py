# -*- coding: utf-8 -*-
"""Построение всех деталей и сборки. Запускать из папки проекта:

    python build.py
    python build.py 01_Основание       только одну деталь

SolidWorks должен быть запущен заранее; Python — 64-bit с pywin32.

KIT — корень набора solidworks (папка его SKILL.md); вписывается при
копировании шаблона в проект. Пока шаблон лежит в наборе, корень находится
от этого файла. Переменные окружения не читаются: устаревшая ведёт в
пустоту (skill-skill, 30-01).
"""
import os
import sys

KIT = None


def kit_root():
    """Корень набора: KIT, иначе на два уровня выше папки шаблона."""
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (KIT, os.path.dirname(os.path.dirname(here))):
        if cand and os.path.isdir(os.path.join(cand, "swkit")):
            return cand
    raise RuntimeError(
        "корень набора solidworks не найден: впишите в KIT в начале build.py "
        "папку SKILL.md набора")


sys.path.insert(0, kit_root())
import swkit as sw

import params

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS_DIR = os.path.join(HERE, "detali")
VIEWS_DIR = os.path.join(HERE, "vidy")
EXPORT_DIR = os.path.join(HERE, "export")
ASM_PATH = os.path.join(HERE, "Сборка.SLDASM")


def build_part(app, name, mat, rect, z0, z1, cuts):
    """Построить одну деталь, проверить и сохранить. Возвращает (путь, ок)."""
    doc = sw.new_part(app)

    # 1. контур и вытяжка от отметки z0 до z1
    with sw.Sketch(doc, sw.TOP) as sk:
        sk.rect(*rect)
    sw.extrude(doc, sk.feature, depth=z1 - z0, start_offset=z0)

    # 2. проёмы
    for (cx1, cy1, cx2, cy2, cz0, cz1) in cuts:
        with sw.Sketch(doc, sw.TOP) as cs:
            cs.rect(cx1, cy1, cx2, cy2)
        sw.cut(doc, cs.feature, depth=cz1 - cz0, end=sw.BLIND,
               start_offset=cz0)

    # 3. материал — только ПОСЛЕ появления тела
    sw.set_material(doc, sw.materials.DEFAULT_DB, mat,
                    expect_density=params.DENSITY[mat])
    sw.set_color(doc, params.COLOR[mat])

    # 4. проверка числом, независимым расчётом
    ok = sw.check_part(
        doc, name,
        expect_volume_mm3=params.expected_volume(rect, z0, z1, cuts),
        expect_box_mm=params.expected_box(rect, z0, z1),
        expect_bodies=1,
        verbose=True)

    # 5. сохранить в любом случае — файл с ошибкой нужен, чтобы посмотреть
    path = sw.save_as(doc, os.path.join(PARTS_DIR, name + ".SLDPRT"))
    sw.shot(doc, os.path.join(VIEWS_DIR, name + "_iso.png"), view="iso")
    sw.close(app, doc)
    return path, ok


def build_assembly(app, paths):
    """Собрать детали сопряжениями базовых плоскостей (способ 3)."""
    asm = sw.new_assembly(app)
    sw.save_as(asm, ASM_PATH)            # ДО вставки: имя входит в адресацию
    sw.preload(app, ASM_PATH, paths)     # детали должны быть открыты
    asm = app.ActiveDoc

    bad_total = 0
    for p in paths:
        _comp, ok, bad = sw.by_origin_mates(app, asm, ASM_PATH, p)
        bad_total += bad
        print("  %-28s сопряжений %d, ошибок %d"
              % (os.path.basename(p), ok, bad))

    sw.rebuild(asm)
    sw.save_as(asm, ASM_PATH)
    print("статусы:", sw.status_report(asm))
    ok = sw.check_assembly(asm, "Сборка", expect_components=len(paths))
    sw.shot(asm, os.path.join(VIEWS_DIR, "сборка_iso.png"), view="iso")
    return asm, (ok and bad_total == 0)


def main():
    sw.utf8_console()
    for d in (PARTS_DIR, VIEWS_DIR, EXPORT_DIR):
        os.makedirs(d, exist_ok=True)

    want = sys.argv[1:]
    app = sw.app(verbose=True)
    sw.close_all(app)

    print("\n=== детали ===")
    paths, failed = [], []
    for spec in params.PARTS:
        if want and spec[0] not in want:
            continue
        try:
            path, ok = build_part(app, *spec)
            paths.append(path)
            if not ok:
                failed.append(spec[0])
        except Exception as e:
            print("  ОШИБКА %-24s %s" % (spec[0], str(e)[:70]))
            failed.append(spec[0])
            sw.close_all(app)

    if want:
        print("\nпостроено выборочно, сборка пропущена")
        return 1 if failed else 0

    print("\n=== сборка ===")
    sw.close_all(app)
    asm, asm_ok = build_assembly(app, paths)

    print("\n=== экспорт ===")
    sw.export(asm, os.path.join(EXPORT_DIR, "Сборка.STEP"))

    print("\n=== итог ===")
    print("деталей построено: %d из %d" % (len(paths), len(params.PARTS)))
    if failed:
        print("НЕ ПРОШЛИ ПРОВЕРКУ: " + ", ".join(failed))
    print("сборка: " + ("в порядке" if asm_ok else "ЕСТЬ ПРОБЛЕМЫ"))
    print("\nПосмотрите виды в %s — числа не скажут, похоже ли это на "
          "задуманное." % VIEWS_DIR)
    return 0 if (not failed and asm_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
