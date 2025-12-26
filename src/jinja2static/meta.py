import logging

import jinja2
from jinja2 import meta, FileSystemLoader, Environment

from collections import defaultdict
from .config import Config


logger = logging.getLogger(__name__)


def find_all_subtemplates(config: Config, template_name):
    """
    Recursively finds all templates referenced by the given template.
    
    :param env: The Jinja2 Environment instance.
    :param template_name: The name of the starting template.
    :return: A set of all referenced template names.
    """
    env = Environment(loader=FileSystemLoader(config.templates))
    found_templates = set()
    unprocessed_templates = {template_name}

    while unprocessed_templates:
        current_template_name = unprocessed_templates.pop()
        if current_template_name in found_templates:
            continue
        
        # Add to the set of processed templates
        found_templates.add(current_template_name)

        try:
            # Get the source and AST (Abstract Syntax Tree)
            source, filename, uptodate = env.loader.get_source(env, current_template_name)
            ast = env.parse(source)
            
            # Find all templates referenced in the current AST
            referenced = meta.find_referenced_templates(ast)
            
            # Add new, unprocessed templates to the queue
            for ref in referenced:
                if ref is not None and ref not in found_templates:
                    unprocessed_templates.add(ref)

        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error(f"Unable to process template: {e}")
            # Handle cases where a referenced template doesn't exist
        except jinja2.exceptions.TemplateNotFound:
            logger.warning(f"Referenced template '{current_template_name}' not found.")
            continue
    
    # Remove the initial template from the result set if you only want subtemplates
    found_templates.discard(template_name)
    return found_templates


def dependency_graph(config: Config):                             
    parent_to_child = {
        page: find_all_subtemplates(config, page)
        for page in config.pages
    }
    child_to_parent = defaultdict(set)
    for original_key, value_set in parent_to_child.items():
        for value in value_set:
            child_to_parent[value].add(original_key)
    return dict(child_to_parent)
