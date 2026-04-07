"""
NFS2Forge — Translation strings.

Usage:
    from src.i18n.translations import tr, set_language
    set_language("pt_BR")
    print(tr("open_file"))
"""
from __future__ import annotations

_STRINGS: dict[str, dict[str, str]] = {

    # ── Toolbar / menus ────────────────────────────────────────────────────
    "open_file": {
        "en":    "Open GlobalB.lzc",
        "pt_BR": "Abrir GlobalB.lzc",
        "es":    "Abrir GlobalB.lzc",
        "it":    "Apri GlobalB.lzc",
        "fr":    "Ouvrir GlobalB.lzc",
        "ru":    "Открыть GlobalB.lzc",
    },
    "open_file_tip": {
        "en":    "Load GlobalB.lzc from your NFSU2 GLOBAL\\ folder",
        "pt_BR": "Carregar GlobalB.lzc da pasta GLOBAL\\ do NFSU2",
        "es":    "Cargar GlobalB.lzc de la carpeta GLOBAL\\ de NFSU2",
        "it":    "Carica GlobalB.lzc dalla cartella GLOBAL\\ di NFSU2",
        "fr":    "Charger GlobalB.lzc depuis le dossier GLOBAL\\ de NFSU2",
        "ru":    "Загрузить GlobalB.lzc из папки GLOBAL\\ NFSU2",
    },
    "write_file": {
        "en":    "Write to GlobalB.lzc",
        "pt_BR": "Salvar no GlobalB.lzc",
        "es":    "Guardar en GlobalB.lzc",
        "it":    "Scrivi su GlobalB.lzc",
        "fr":    "Écrire dans GlobalB.lzc",
        "ru":    "Записать в GlobalB.lzc",
    },
    "write_file_tip": {
        "en":    "Save all pending changes to GlobalB.lzc (auto-backup created first)",
        "pt_BR": "Salvar todas as alterações no GlobalB.lzc (backup automático criado antes)",
        "es":    "Guardar todos los cambios en GlobalB.lzc (copia de seguridad automática)",
        "it":    "Salva tutte le modifiche su GlobalB.lzc (backup automatico creato prima)",
        "fr":    "Enregistrer les modifications dans GlobalB.lzc (sauvegarde automatique)",
        "ru":    "Сохранить изменения в GlobalB.lzc (автобэкап создаётся заранее)",
    },
    "language": {
        "en":    "Language",
        "pt_BR": "Idioma",
        "es":    "Idioma",
        "it":    "Lingua",
        "fr":    "Langue",
        "ru":    "Язык",
    },
    "about": {
        "en":    "About",
        "pt_BR": "Sobre",
        "es":    "Acerca de",
        "it":    "Informazioni",
        "fr":    "À propos",
        "ru":    "О программе",
    },

    # ── Status bar ─────────────────────────────────────────────────────────
    "status_ready": {
        "en":    "Open GlobalB.lzc to begin  (File → Open GlobalB.lzc)",
        "pt_BR": "Abra o GlobalB.lzc para começar  (Arquivo → Abrir GlobalB.lzc)",
        "es":    "Abre GlobalB.lzc para comenzar  (Archivo → Abrir GlobalB.lzc)",
        "it":    "Apri GlobalB.lzc per iniziare  (File → Apri GlobalB.lzc)",
        "fr":    "Ouvrez GlobalB.lzc pour commencer  (Fichier → Ouvrir GlobalB.lzc)",
        "ru":    "Откройте GlobalB.lzc для начала работы",
    },
    "status_editing": {
        "en":    "Editing",
        "pt_BR": "Editando",
        "es":    "Editando",
        "it":    "Modifica",
        "fr":    "Modification",
        "ru":    "Редактирование",
    },
    "status_unsaved": {
        "en":    "Unsaved changes",
        "pt_BR": "Alterações não salvas",
        "es":    "Cambios sin guardar",
        "it":    "Modifiche non salvate",
        "fr":    "Modifications non enregistrées",
        "ru":    "Несохранённые изменения",
    },
    "status_saved": {
        "en":    "Saved",
        "pt_BR": "Salvo",
        "es":    "Guardado",
        "it":    "Salvato",
        "fr":    "Enregistré",
        "ru":    "Сохранено",
    },
    "status_backup": {
        "en":    "backup",
        "pt_BR": "backup",
        "es":    "copia de seguridad",
        "it":    "backup",
        "fr":    "sauvegarde",
        "ru":    "бэкап",
    },
    "cars_available": {
        "en":    "cars available",
        "pt_BR": "carros disponíveis",
        "es":    "autos disponibles",
        "it":    "auto disponibili",
        "fr":    "voitures disponibles",
        "ru":    "автомобилей доступно",
    },

    # ── Dialogs ────────────────────────────────────────────────────────────
    "unsaved_title": {
        "en":    "Unsaved Changes",
        "pt_BR": "Alterações não salvas",
        "es":    "Cambios sin guardar",
        "it":    "Modifiche non salvate",
        "fr":    "Modifications non enregistrées",
        "ru":    "Несохранённые изменения",
    },
    "unsaved_body": {
        "en":    "You have unsaved changes to GlobalB.lzc.\nClose without saving?",
        "pt_BR": "Você tem alterações não salvas no GlobalB.lzc.\nFechar sem salvar?",
        "es":    "Tienes cambios sin guardar en GlobalB.lzc.\n¿Cerrar sin guardar?",
        "it":    "Hai modifiche non salvate su GlobalB.lzc.\nChiudere senza salvare?",
        "fr":    "Vous avez des modifications non enregistrées dans GlobalB.lzc.\nFermer sans enregistrer?",
        "ru":    "В GlobalB.lzc есть несохранённые изменения.\nЗакрыть без сохранения?",
    },
    "saved_title": {
        "en":    "Saved",
        "pt_BR": "Salvo",
        "es":    "Guardado",
        "it":    "Salvato",
        "fr":    "Enregistré",
        "ru":    "Сохранено",
    },
    "saved_body": {
        "en":    "GlobalB.lzc written successfully.\nBackup: {bak}",
        "pt_BR": "GlobalB.lzc salvo com sucesso.\nBackup: {bak}",
        "es":    "GlobalB.lzc guardado correctamente.\nCopia de seguridad: {bak}",
        "it":    "GlobalB.lzc scritto con successo.\nBackup: {bak}",
        "fr":    "GlobalB.lzc enregistré avec succès.\nSauvegarde : {bak}",
        "ru":    "GlobalB.lzc успешно записан.\nБэкап: {bak}",
    },
    "backup_failed_title": {
        "en":    "Backup Failed",
        "pt_BR": "Falha no Backup",
        "es":    "Error de copia de seguridad",
        "it":    "Backup fallito",
        "fr":    "Échec de la sauvegarde",
        "ru":    "Ошибка бэкапа",
    },
    "backup_failed_body": {
        "en":    "Could not create backup:\n{err}\n\nSave aborted.",
        "pt_BR": "Não foi possível criar o backup:\n{err}\n\nSalvamento cancelado.",
        "es":    "No se pudo crear la copia de seguridad:\n{err}\n\nGuardado cancelado.",
        "it":    "Impossibile creare il backup:\n{err}\n\nSalvataggio annullato.",
        "fr":    "Impossible de créer la sauvegarde :\n{err}\n\nEnregistrement annulé.",
        "ru":    "Не удалось создать бэкап:\n{err}\n\nСохранение отменено.",
    },
    "invalid_file_title": {
        "en":    "Invalid File",
        "pt_BR": "Arquivo Inválido",
        "es":    "Archivo no válido",
        "it":    "File non valido",
        "fr":    "Fichier invalide",
        "ru":    "Неверный файл",
    },
    "load_error_title": {
        "en":    "Load Error",
        "pt_BR": "Erro ao Carregar",
        "es":    "Error de carga",
        "it":    "Errore di caricamento",
        "fr":    "Erreur de chargement",
        "ru":    "Ошибка загрузки",
    },
    "load_error_body": {
        "en":    "Failed to load GlobalB.lzc:\n{err}",
        "pt_BR": "Falha ao carregar GlobalB.lzc:\n{err}",
        "es":    "Error al cargar GlobalB.lzc:\n{err}",
        "it":    "Errore nel caricamento di GlobalB.lzc:\n{err}",
        "fr":    "Échec du chargement de GlobalB.lzc :\n{err}",
        "ru":    "Ошибка загрузки GlobalB.lzc:\n{err}",
    },
    "save_error_title": {
        "en":    "Save Error",
        "pt_BR": "Erro ao Salvar",
        "es":    "Error al guardar",
        "it":    "Errore di salvataggio",
        "fr":    "Erreur d'enregistrement",
        "ru":    "Ошибка сохранения",
    },

    # ── Sidebar ────────────────────────────────────────────────────────────
    "vehicles": {
        "en":    "VEHICLES",
        "pt_BR": "VEÍCULOS",
        "es":    "VEHÍCULOS",
        "it":    "VEICOLI",
        "fr":    "VÉHICULES",
        "ru":    "АВТОМОБИЛИ",
    },
    "search_placeholder": {
        "en":    "Search cars...",
        "pt_BR": "Buscar carros...",
        "es":    "Buscar autos...",
        "it":    "Cerca auto...",
        "fr":    "Rechercher des voitures...",
        "ru":    "Поиск авто...",
    },
    "cars_count_singular": {
        "en":    "{n} car",
        "pt_BR": "{n} carro",
        "es":    "{n} auto",
        "it":    "{n} auto",
        "fr":    "{n} voiture",
        "ru":    "{n} авто",
    },
    "cars_count_plural": {
        "en":    "{n} cars",
        "pt_BR": "{n} carros",
        "es":    "{n} autos",
        "it":    "{n} auto",
        "fr":    "{n} voitures",
        "ru":    "{n} авто",
    },

    # ── Editor panel ───────────────────────────────────────────────────────
    "welcome_title": {
        "en":    "NFS2Forge",
        "pt_BR": "NFS2Forge",
        "es":    "NFS2Forge",
        "it":    "NFS2Forge",
        "fr":    "NFS2Forge",
        "ru":    "NFS2Forge",
    },
    "welcome_msg": {
        "en":    "1 · Open GlobalB.lzc from the toolbar\n2 · Select a car from the list\n3 · Edit parameters and click Write",
        "pt_BR": "1 · Abra o GlobalB.lzc pela barra de ferramentas\n2 · Selecione um carro na lista\n3 · Edite os parâmetros e clique em Salvar",
        "es":    "1 · Abre GlobalB.lzc desde la barra de herramientas\n2 · Selecciona un auto de la lista\n3 · Edita los parámetros y haz clic en Guardar",
        "it":    "1 · Apri GlobalB.lzc dalla barra degli strumenti\n2 · Seleziona un'auto dall'elenco\n3 · Modifica i parametri e clicca Scrivi",
        "fr":    "1 · Ouvrez GlobalB.lzc depuis la barre d'outils\n2 · Sélectionnez une voiture dans la liste\n3 · Modifiez les paramètres et cliquez sur Écrire",
        "ru":    "1 · Откройте GlobalB.lzc через панель инструментов\n2 · Выберите автомобиль из списка\n3 · Измените параметры и нажмите Записать",
    },
    "group_chassis": {
        "en":    "Chassis",
        "pt_BR": "Chassi",
        "es":    "Chasis",
        "it":    "Telaio",
        "fr":    "Châssis",
        "ru":    "Шасси",
    },
    "group_engine": {
        "en":    "Engine",
        "pt_BR": "Motor",
        "es":    "Motor",
        "it":    "Motore",
        "fr":    "Moteur",
        "ru":    "Двигатель",
    },
    "group_gearbox": {
        "en":    "Gearbox",
        "pt_BR": "Câmbio",
        "es":    "Caja de cambios",
        "it":    "Cambio",
        "fr":    "Boîte de vitesses",
        "ru":    "КПП",
    },
    "group_handling": {
        "en":    "Handling",
        "pt_BR": "Dirigibilidade",
        "es":    "Manejo",
        "it":    "Maneggevolezza",
        "fr":    "Comportement",
        "ru":    "Управляемость",
    },
    "btn_reset": {
        "en":    "↺  Reset",
        "pt_BR": "↺  Resetar",
        "es":    "↺  Reiniciar",
        "it":    "↺  Ripristina",
        "fr":    "↺  Réinitialiser",
        "ru":    "↺  Сброс",
    },
    "btn_write": {
        "en":    "💾  Write to GlobalB.lzc",
        "pt_BR": "💾  Salvar no GlobalB.lzc",
        "es":    "💾  Guardar en GlobalB.lzc",
        "it":    "💾  Scrivi su GlobalB.lzc",
        "fr":    "💾  Écrire dans GlobalB.lzc",
        "ru":    "💾  Записать в GlobalB.lzc",
    },
    "dirty_label": {
        "en":    "● unsaved changes",
        "pt_BR": "● alterações não salvas",
        "es":    "● cambios sin guardar",
        "it":    "● modifiche non salvate",
        "fr":    "● modifications non enregistrées",
        "ru":    "● несохранённые изменения",
    },
    "not_found": {
        "en":    "identifier not found in GlobalB.lzc",
        "pt_BR": "identificador não encontrado no GlobalB.lzc",
        "es":    "identificador no encontrado en GlobalB.lzc",
        "it":    "identificatore non trovato in GlobalB.lzc",
        "fr":    "identifiant introuvable dans GlobalB.lzc",
        "ru":    "идентификатор не найден в GlobalB.lzc",
    },
    "editable_fields": {
        "en":    "editable fields",
        "pt_BR": "campos editáveis",
        "es":    "campos editables",
        "it":    "campi modificabili",
        "fr":    "champs modifiables",
        "ru":    "редактируемых полей",
    },
    "speed_gearbox": {
        "en":    "-speed gearbox",
        "pt_BR": "-velocidades",
        "es":    " velocidades",
        "it":    " marce",
        "fr":    " vitesses",
        "ru":    "-ступенч. КПП",
    },

    # ── Field labels ───────────────────────────────────────────────────────
    "field_mass": {
        "en":    "Mass",
        "pt_BR": "Massa",
        "es":    "Masa",
        "it":    "Massa",
        "fr":    "Masse",
        "ru":    "Масса",
    },
    "field_brake_force": {
        "en":    "Brake Force",
        "pt_BR": "Força de Freio",
        "es":    "Fuerza de Freno",
        "it":    "Forza Frenante",
        "fr":    "Force de Freinage",
        "ru":    "Тормозное усилие",
    },
    "field_cog_height": {
        "en":    "CoG Height",
        "pt_BR": "Altura do CG",
        "es":    "Altura del CdG",
        "it":    "Altezza CdG",
        "fr":    "Hauteur CdG",
        "ru":    "Высота ЦТ",
    },
    "field_peak_rpm": {
        "en":    "Peak RPM",
        "pt_BR": "RPM de Pico",
        "es":    "RPM de pico",
        "it":    "RPM di picco",
        "fr":    "RPM de pointe",
        "ru":    "Пиковые об/мин",
    },
    "field_max_rpm": {
        "en":    "Max RPM",
        "pt_BR": "RPM Máximo",
        "es":    "RPM máximo",
        "it":    "RPM massimo",
        "fr":    "RPM maximum",
        "ru":    "Макс. об/мин",
    },
    "field_grip_front": {
        "en":    "Front Grip",
        "pt_BR": "Grip Dianteiro",
        "es":    "Agarre delantero",
        "it":    "Grip anteriore",
        "fr":    "Adhérence avant",
        "ru":    "Сцепление перед.",
    },
    "field_grip_rear": {
        "en":    "Rear Grip",
        "pt_BR": "Grip Traseiro",
        "es":    "Agarre trasero",
        "it":    "Grip posteriore",
        "fr":    "Adhérence arrière",
        "ru":    "Сцепление зад.",
    },
    "field_steer_lock": {
        "en":    "Steer Lock",
        "pt_BR": "Ângulo de Direção",
        "es":    "Ángulo de dirección",
        "it":    "Angolo sterzata",
        "fr":    "Angle de braquage",
        "ru":    "Угол поворота",
    },
    "field_spring_front": {
        "en":    "Spring Front",
        "pt_BR": "Mola Dianteira",
        "es":    "Resorte delantero",
        "it":    "Molla anteriore",
        "fr":    "Ressort avant",
        "ru":    "Пружина перед.",
    },
    "field_damper_front": {
        "en":    "Damper Front",
        "pt_BR": "Amortecedor Diant.",
        "es":    "Amortiguador del.",
        "it":    "Ammortizzatore ant.",
        "fr":    "Amortisseur avant",
        "ru":    "Демпфер перед.",
    },
    "field_spring_rear": {
        "en":    "Spring Rear",
        "pt_BR": "Mola Traseira",
        "es":    "Resorte trasero",
        "it":    "Molla posteriore",
        "fr":    "Ressort arrière",
        "ru":    "Пружина зад.",
    },
    "field_damper_rear": {
        "en":    "Damper Rear",
        "pt_BR": "Amortecedor Tras.",
        "es":    "Amortiguador tra.",
        "it":    "Ammortizzatore pos.",
        "fr":    "Amortisseur arrière",
        "ru":    "Демпфер зад.",
    },

    # ── Stat bar labels ────────────────────────────────────────────────────
    "stat_accel": {
        "en":    "Acceleration",
        "pt_BR": "Aceleração",
        "es":    "Aceleración",
        "it":    "Accelerazione",
        "fr":    "Accélération",
        "ru":    "Разгон",
    },
    "stat_speed": {
        "en":    "Top Speed",
        "pt_BR": "Velocidade Máx.",
        "es":    "Velocidad máx.",
        "it":    "Velocità massima",
        "fr":    "Vitesse max.",
        "ru":    "Макс. скорость",
    },
    "stat_handling": {
        "en":    "Handling",
        "pt_BR": "Dirigibilidade",
        "es":    "Manejo",
        "it":    "Maneggevolezza",
        "fr":    "Comportement",
        "ru":    "Управляемость",
    },
    "stat_braking": {
        "en":    "Braking",
        "pt_BR": "Frenagem",
        "es":    "Frenado",
        "it":    "Frenata",
        "fr":    "Freinage",
        "ru":    "Торможение",
    },
    "stat_drift": {
        "en":    "Drift",
        "pt_BR": "Drift",
        "es":    "Drift",
        "it":    "Drift",
        "fr":    "Drift",
        "ru":    "Дрифт",
    },
}

# ── Language state ─────────────────────────────────────────────────────────
AVAILABLE_LANGUAGES: dict[str, str] = {
    "en":    "English",
    "pt_BR": "Português (BR)",
    "es":    "Español",
    "it":    "Italiano",
    "fr":    "Français",
    "ru":    "Русский",
}

_current_lang: str = "en"


def set_language(lang: str) -> None:
    global _current_lang
    if lang in AVAILABLE_LANGUAGES:
        _current_lang = lang


def get_language() -> str:
    return _current_lang


def tr(key: str, **kwargs) -> str:
    """Return the translation for *key* in the current language.

    Falls back to English if the key or language is missing.
    Supports .format()-style placeholders via **kwargs.
    """
    entry = _STRINGS.get(key, {})
    text = entry.get(_current_lang) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
