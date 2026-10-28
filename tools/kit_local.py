# -*- coding: utf-8 -*-
"""Особое для набора solidworks в общей проверке skill-skill/tools/check_docs.py.

PROJECT_EXT — имена моделей и экспорта в папке проекта (--project или
`git config solidworks.project`) становятся стоп-словами: имена деталей и
сборок выдают изделие (40-02).
"""
GENERIC = set()
TEXT_EXT = ()
PROJECT_EXT = (".SLDPRT", ".SLDASM", ".SLDDRW", ".STEP")


def extra_checks(root):
    return []
