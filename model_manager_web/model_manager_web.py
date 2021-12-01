# All entity numbers are listed in the order of these entities on the platform


import PySimpleGUIWeb as sg

import requests

url = ""  # paste server url
headers = {"Authorization": """"""}  # paste bearer certificate
update_delay = 500

mcs_model_id = ""  # paste your mcs model id
psms_model_id = ""  # paste your psms model id

all_models = []
all_objects = []


def pars_order_and_names(pars_data):
    names_and_order_list = []
    for iter in pars_data:
        names_and_order_list.append(str(1 + len(names_and_order_list)) + ": " + iter["name"])
    return names_and_order_list


def elem_of_list_with_max_len(cur_list):
    return max(map(lambda x: len(x), cur_list))


def yes_or_no_bool(cur_bool):
    if type(cur_bool) != bool:
        return cur_bool
    return "Да" if cur_bool else "Нет"


def win_select(listbox_list, name_of_listbox):
    if not listbox_list:
        if name_of_listbox == "модель":
            sg.popup("Модели отсутвуют")
        elif name_of_listbox == "объект":
            sg.popup("Объектов с такой моделью не существует")
        else:
            sg.popup("Нет таких " + name_of_listbox)
        return "", "restart"
    sg.theme("Dark Blue 3")
    layout = [[sg.Text("Выберите " + name_of_listbox + ":"), ],
              [sg.Listbox(values=listbox_list, size=(elem_of_list_with_max_len(listbox_list), len(listbox_list)))],
              [sg.Button("Ok")]]
    cur_window = sg.Window("Мониторинг состояния объектов", layout, font=("Helvetica", 25),
                           default_element_size=(40, 1), grab_anywhere=False)
    while True:
        event, values = cur_window.read()
        if event == sg.WIN_CLOSED:
            return "", "exit"
        elif event == "Ok" and values[0] != []:
            selected_elem = values[0][0]
            return selected_elem, "next"


def mcs_win(cur_obj):
    cur_obj_state = cur_obj.get("state", {})
    sg.theme("Dark Blue 3")
    layout = [[sg.Text(f'Объект: {cur_obj.get("name", "---")};               ID объекта: {cur_obj.get("_id", "---")}',
                       size=(70, 1),
                       key='obj_and_id_mod')],
              [sg.Text(
                  f'Онлайн: {yes_or_no_bool(cur_obj_state.get("online", "---"))};                                       '
                  f'              Состояние бота: '
                  f'{"Работает" if cur_obj.get("bot", {}).get("state", "---") == "running" else "Выключен"}',
                  size=(70, 1), key='online_and_bot')],
              [sg.Text(
                  f'Электропитание подано: {yes_or_no_bool(cur_obj_state.get("electro", "---"))};                       '
                  f'    Вентиляция включена: '
                  f'{yes_or_no_bool(cur_obj_state.get("ventilation", "---"))}',
                  size=(70, 1), key='electro_and_ventilation')],
              [sg.Text(
                  f'Сигнализация включена: {yes_or_no_bool(cur_obj_state.get("buzzer", "---"))};                        '
                  f'   Уровень шума: {cur_obj_state.get("noise", "---")} дБ',
                  size=(70, 1), key='noize_and_moves')],
              [sg.Combo(("Температура породы №1", "Температура породы №2"), size=(25, 1), key='temp_of_ores'),
               sg.Text("          ", size=(10, 1), key='temp_of_sel_ore'),
               sg.Combo(("Движение породы №1", "Движение породы №2", "Движение породы №3", "Движение породы №4"),
                        size=(25, 1), key='move_of_ores'),
               sg.Text(" ", size=(8, 1), key='move_of_sel_ore')],
              [sg.Button("Вернуться к выбору модели")], ]
    cur_window = sg.Window("Мониторинг состояния объектов", layout, font=("Helvetica", 25),
                           default_element_size=(20, 1), grab_anywhere=False)
    while True:
        event, values = cur_window.read(update_delay)
        if event == sg.WIN_CLOSED:
            return "exit"
        if event == "Вернуться к выбору модели":
            return "restart"
        cur_obj_state = cur_obj.get("state", {})
        cur_obj = requests.get(url + "/api/v1/objects/" + cur_obj["_id"], headers=headers).json()
        if values.get("temp_of_ores", False) == "Температура породы №1":
            cur_window["temp_of_sel_ore"].update(f' {cur_obj_state.get("temp1", "---")} °C         ')
        elif values.get("temp_of_ores", False) == "Температура породы №2":
            cur_window["temp_of_sel_ore"].update(f' {cur_obj_state.get("temp2", "---")} °C         ')
        else:
            cur_window["temp_of_sel_ore"].update("         ")

        if values.get("move_of_ores", False) == "Движение породы №1":
            cur_window["move_of_sel_ore"].update(f' {yes_or_no_bool(cur_obj_state.get("move1", "---"))}')
        elif values.get("move_of_ores", False) == "Движение породы №2":
            cur_window["move_of_sel_ore"].update(f' {yes_or_no_bool(cur_obj_state.get("move2", "---"))}')
        elif values.get("move_of_ores", False) == "Движение породы №3":
            cur_window["move_of_sel_ore"].update(f' {yes_or_no_bool(cur_obj_state.get("move3", "---"))}')
        elif values.get("move_of_ores", False) == "Движение породы №4":
            cur_window["move_of_sel_ore"].update(f' {yes_or_no_bool(cur_obj_state.get("move4", "---"))}')
        else:
            cur_window["move_of_sel_ore"].update(" ")

        cur_window["obj_and_id_mod"].update(
            f'Объект: {cur_obj.get("name", "---")};            ID объекта: {cur_obj.get("_id", "---")}')
        cur_window["online_and_bot"].update(
            f'Онлайн: {yes_or_no_bool(cur_obj_state.get("online", "---"))};             '
            f'                          '
            f'              Состояние бота: '
            f'{"Работает" if cur_obj.get("bot", {}).get("state", "---") == "running" else "Выключен"}')
        cur_window["electro_and_ventilation"].update(
            f'Электропитание подано: {yes_or_no_bool(cur_obj_state.get("electro", "---"))};                       '
            f'    Вентиляция включена: '
            f'{yes_or_no_bool(cur_obj_state.get("ventilation", "---"))}')
        cur_window["noize_and_moves"].update(
            f'Сигнализация включена: {yes_or_no_bool(cur_obj_state.get("buzzer", "---"))};                        '
            f'   Уровень шума: {cur_obj_state.get("noise", "---")} дБ')


def psms_win(cur_obj):
    sg.popup("Интерфейс ещё не разработан")
    return "", "restart"


while True:
    all_models = requests.get(url + "/api/v1/models", headers=headers).json()
    all_models_names = pars_order_and_names(all_models)
    name_of_sel_mod, command_win_select = win_select(all_models_names, "модель")
    if command_win_select == "restart":
        continue
    elif command_win_select == "exit":
        break
    command_win_select = ""
    id_of_sel_model = all_models[int(name_of_sel_mod[0]) - 1]["_id"]
    all_objects = requests.get(url + "/api/v1/objects", headers=headers).json()
    objects_of_sel_mod = list(filter(lambda x: x["model"] == id_of_sel_model, all_objects))
    object_names_of_sel_mod = pars_order_and_names(objects_of_sel_mod)
    name_of_sel_obj, command_win_select = win_select(object_names_of_sel_mod, "объект")
    if command_win_select == "restart":
        continue
    elif command_win_select == "exit":
        break
    command_win_select = ""
    sel_obj = objects_of_sel_mod[int(name_of_sel_obj[0]) - 1]
    if id_of_sel_model == mcs_model_id:
        command_viewer_win = mcs_win(sel_obj)
    elif id_of_sel_model == psms_model_id:
        command_viewer_win = psms_win(sel_obj)
    else:
        sg.popup("Для данного объекта нет интерфейса")
        continue
    if command_viewer_win == "restart":
        continue
    if command_viewer_win == "exit":
        break
    command_viewer_win = ""
