# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import webbrowser

import pygraphviz

import rose.config
import rose.external
import rose.macro
import rose.macros.trigger
import rose.opt_parse
import rose.reporter


def get_node_state_attrs(config, section, option=None, allowed_sections=None):
    node_attrs = {}
    if option is None:
        node_attrs["shape"] = "octagon"
    if not config.value.keys():
        # Empty configuration - we can assume pure metadata.
        return node_attrs
    if allowed_sections is None:
        allowed_sections = []
    normal_state = rose.config.ConfigNode.STATE_NORMAL
    config_section_node = config.get([section])
    id_ = rose.macro.get_id_from_section_option(section, option)
    state = ""
    is_section_ignored = False
    is_trigger_ignored = False
    is_user_ignored = False
    is_missing = False
    if (config_section_node is not None and
            config_section_node.state != normal_state and
            option is not None):
        state = "^"
        is_section_ignored = True
    config_node = config.get([section, option])
    if config_node is None:
        is_missing = True
    elif config_node.state != normal_state:
        state += config_node.state
        if config_node.state == config_node.STATE_USER_IGNORED:
            is_user_ignored = True
        if config_node.state == config_node.STATE_SYST_IGNORED:
            is_trigger_ignored = True
    if allowed_sections and section not in allowed_sections:
        node_attrs["shape"] = "rectangle"
    if state:
        node_attrs["label"] = state + id_
    if is_missing:
        node_attrs["color"] = "grey"
    elif is_trigger_ignored or is_section_ignored:
        node_attrs["color"] = "red"
    elif is_user_ignored:
        node_attrs["color"] = "orange"
    else:
        node_attrs["color"] = "green"
    return node_attrs


def get_graph(config, meta_config, allowed_sections=None,
              allowed_properties=None, err_reporter=None):
    if allowed_sections is None:
        allowed_sections = []
    if allowed_properties is None:
        allowed_properties = []
    if err_reporter is None:
        err_reporter = rose.reporter.Reporter()
    graph = pygraphviz.AGraph(directed=True)
    graph.graph_attr['rankdir'] = "LR"
    if not allowed_properties or (
            allowed_properties and "trigger" in allowed_properties):
        get_trigger_graph(graph, config, meta_config,
                          err_reporter, allowed_sections=allowed_sections)
    return graph


def get_trigger_graph(graph, config, meta_config, err_reporter,
                      allowed_sections=None):
    trigger = rose.macros.trigger.TriggerMacro()
    bad_reports = trigger.validate_dependencies(config, meta_config)
    if bad_reports:
        err_reporter(rose.macro.get_reports_as_text(
                     bad_reports, "trigger.TriggerMacro"))
        return None
    ids = []
    for keylist, node in meta_config.walk(no_ignore=True):
        id_ = keylist[0]
        if isinstance(node.value, dict):
            section, option = (
                rose.macro.get_section_option_from_id(id_))
            if not allowed_sections or (
                    allowed_sections and section in allowed_sections):
                ids.append(id_)
    ids.sort(rose.config.sort_settings)
    delim = rose.CONFIG_DELIMITER
    for id_ in ids:
        section, option = rose.macro.get_section_option_from_id(id_)
        node_attrs = get_node_state_attrs(
            config, section, option,
            allowed_sections=allowed_sections
        )
        graph.add_node(id_, **node_attrs)
    for setting_id, id_value_dict in sorted(
            trigger.trigger_family_lookup.items()):
        section, option = rose.macro.get_section_option_from_id(setting_id)
        node = config.get([section, option])
        if node is None:
            setting_value = None
        else:
            setting_value = node.value
        setting_is_section_ignored = (
            config.get([section], no_ignore=True) is None)
        for dependent_id, values in sorted(id_value_dict.items()):
            dep_section, dep_option = rose.macro.get_section_option_from_id(
                dependent_id)
            if allowed_sections:
                if (section not in allowed_sections and
                        dep_section not in allowed_sections):
                    continue
            if not values:
                values = [None]
            has_success = False
            if setting_value is not None:
                for value in values:
                    if ((value is None and node.state == node.STATE_NORMAL and
                             not setting_is_section_ignored) or 
                            trigger._check_values_ok(
                                setting_value, setting_id, [value])):
                        has_success = True
            for value in values:
                value_id = setting_id + "=" + str(value)
                dependent_attrs = {}
                if setting_value is None:
                    dependent_attrs["color"] = "grey"
                else:
                    if ((value is None and node.state == node.STATE_NORMAL and
                             not setting_is_section_ignored) or 
                            trigger._check_values_ok(
                                setting_value, setting_id, [value])):
                        dependent_attrs["color"] = "green"
                    else:
                        dependent_attrs["color"] = "red"
                if not graph.has_node(setting_id):
                    node_attrs = get_node_state_attrs(
                        config, section, option,
                        allowed_sections=allowed_sections
                    )
                    graph.add_node(setting_id, **node_attrs)
                if not graph.has_node(dependent_id):
                    node_attrs = get_node_state_attrs(
                        config, dep_section, dep_option,
                        allowed_sections=allowed_sections
                    )
                    graph.add_node(dependent_id, **node_attrs)
                if not graph.has_node(value_id):
                    node_attrs = {"style": "filled",
                                  "label": value,
                                  "shape": "box"}
                    node_attrs.update(dependent_attrs)
                    graph.add_node(value_id, **node_attrs)
                edge_attrs = {}
                edge_attrs.update(dependent_attrs)
                if setting_value is not None:
                    edge_attrs["label"] = setting_value
                graph.add_edge(setting_id, value_id, **edge_attrs)
                if dependent_attrs["color"] == "red" and has_success:
                    dependent_attrs["arrowhead"] = "empty"
                graph.add_edge(value_id, dependent_id, **dependent_attrs)


def draw_graph(graph, debug_mode=False):
    suffix = ".svg"
    if debug_mode:
        suffix = ".dot"
    image_file_handle = tempfile.NamedTemporaryFile(suffix=suffix)
    graph.draw(image_file_handle.name, prog='dot')
    image_file_handle.seek(0)
    if debug_mode:
        text = image_file_handle.read()
        image_file_handle.close()
        print text
        return
    rose.external.launch_image_viewer(image_file_handle.name, run_fg=True)


def exit_fail():
    text = rose.macro.ERROR_LOAD_METADATA.format("")
    rose.reporter.Reporter()(text,
                             kind=rose.reporter.Reporter.KIND_ERR,
                             level=rose.reporter.Reporter.FAIL)
    sys.exit(1)


if __name__ == "__main__":
    rose.macro.add_site_meta_paths()
    rose.macro.add_env_meta_paths()
    opt_parser = rose.opt_parse.RoseOptionParser()
    options = ["conf_dir", "meta_path", "output_dir", "property"]
    opt_parser.add_my_options(*options)
    opts, args = opt_parser.parse_args()
    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    else:
        os.chdir(opts.conf_dir)
    sys.path.append(os.getenv("ROSE_HOME"))
    rose.macro.add_opt_meta_paths(opts.meta_path)
   
    config_file_path = os.path.join(os.getcwd(), rose.SUB_CONFIG_NAME)
    meta_config_file_path = os.path.join(os.getcwd(), rose.META_CONFIG_NAME)
    config_loader = rose.config.ConfigLoader()
    if os.path.exists(config_file_path):
        config = config_loader(config_file_path)
        meta_config = rose.config.ConfigNode()
        meta_path, warning = rose.macro.load_meta_path(
            config, opts.conf_dir)
        if meta_path is None:
            exit_fail()
        meta_config = rose.macro.load_meta_config(
            config,
            directory=opts.conf_dir,
        )
        if not meta_config.value.keys():
            exit_fail()
    elif os.path.exists(meta_config_file_path):
        config = rose.config.ConfigNode()
        meta_config = config_loader(meta_config_file_path)
    else:
        exit_fail()
    graph = get_graph(config, meta_config, allowed_sections=args,
                      allowed_properties=opts.property)
    if graph is None:
        exit_fail()
    draw_graph(graph, debug_mode=opts.debug_mode)
