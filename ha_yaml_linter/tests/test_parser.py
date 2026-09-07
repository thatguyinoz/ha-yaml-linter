import pytest
from src.parser import (
    parse_yaml,
    HASecret,
    HAInclude,
    HAIncludeDirList,
    HAIncludeDirNamed,
    HAIncludeDirMergeList,
    HAIncludeDirMergeNamed,
    HAEnvVar,
)

def test_parse_standard_yaml():
    yaml_str = """
    house:
      rooms: 4
      garage: true
    """
    result = parse_yaml(yaml_str)
    assert result['house']['rooms'] == 4
    assert result['house']['garage'] is True

def test_parse_ha_custom_tags():
    yaml_str = """
    sensor:
      - platform: template
        sensors:
          wifi_password: !secret wifi_password_secret
          main_config: !include config/main.yaml
          sub_configs: !include_dir_list configs/sensors/
          named_configs: !include_dir_named configs/entities/
          merged_lists: !include_dir_merge_list configs/automation_lists/
          merged_named: !include_dir_merge_named configs/scripts/
          api_port: !env_var PORT
    """
    result = parse_yaml(yaml_str)
    sensor_config = result['sensor'][0]['sensors']
    
    assert sensor_config['wifi_password'] == HASecret('wifi_password_secret')
    assert sensor_config['main_config'] == HAInclude('config/main.yaml')
    assert sensor_config['sub_configs'] == HAIncludeDirList('configs/sensors/')
    assert sensor_config['named_configs'] == HAIncludeDirNamed('configs/entities/')
    assert sensor_config['merged_lists'] == HAIncludeDirMergeList('configs/automation_lists/')
    assert sensor_config['merged_named'] == HAIncludeDirMergeNamed('configs/scripts/')
    assert sensor_config['api_port'] == HAEnvVar('PORT')
