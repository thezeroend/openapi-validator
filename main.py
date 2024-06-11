import re
import yaml
from openapi_spec_validator import validate_spec
from ruamel.yaml import YAML
from jsonpath_ng import parse

def load_rules(rules_file):
    with open(rules_file, 'r') as file:
        rules = yaml.safe_load(file)
    return rules['rules']

def load_openapi_spec(openapi_file):
    yaml_loader = YAML()
    with open(openapi_file, 'r') as file:
        spec = yaml_loader.load(file)
    validate_spec(spec)
    return spec

def pattern(value, match):
    return re.match(match, value) is not None

def hasProperty(obj, property):
    return property in obj

def apply_rules(spec, rules):
    errors = []

    def extract(json_path, obj, full_node):
        jsonpath_expr = parse(json_path)
        matches = jsonpath_expr.find(obj)
        for match in matches:
            yield match.value, match.full_path, match.path.fields[-1]

    for rule_id, rule in rules.items():
        for path in rule['given'].split(','):
            for obj, full_node, key in extract(path.strip(), spec, spec):
                if obj is None:
                    continue
                if not eval(rule['then']['function'])(obj, **rule['then']['functionOptions']):
                    errors.append({
                        'codigo': rule_id,
                        'mensagem': rule['description'],
                        'chave': key,
                        'objeto': obj
                    })
    return errors

def main(openapi_file, rules_file):
    rules = load_rules(rules_file)
    spec = load_openapi_spec(openapi_file)
    errors = apply_rules(spec, rules)
    
    if errors:
        for error in errors:
            print(f"Codigo: {error['codigo']}, Mensagem: {error['mensagem']}, Chave: {error['chave']}, Objeto: {error['objeto']}")
    else:
        print("Nenhuma violação de segurança encontrada.")

if __name__ == "__main__":
    main('api_definition.yaml', 'rules.yaml')
