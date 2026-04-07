# Mark 2 Capability Registry and Plugins

## Objetivo
Fazer a plataforma sair de "ações espalhadas" para "capacidades formais e descobríveis".

## Capability metadata mínima
- `capability_name`
- `version`
- `description`
- `owner_runtime`
- `action_names`
- `required_vehicle_type`
- `required_payloads`
- `required_actuators`
- `required_environment`
- `safety_level`
- `status`

## Exemplos de capability futura
- `vehicle.aerial.basic_flight`
- `mission.patrol`
- `mission.delivery`
- `perception.visual_tracking`
- `payload.camera_stream`
- `payload.audio_output`
- `payload.display_avatar`
- `actuator.robotic_arm.basic_control`
- `actuator.robotic_arm.surface_cleaning`
- `interaction.voice_assistant`

## Plugin model
Cada plugin futuro deve poder registrar:
- capabilities
- actions
- read models parciais
- health endpoints
- constraints

## Mark 1 compatibility rule
Mesmo que o registry completo não exista ainda, o Mark 1 deve já tratar capabilities como entidade formalizável.
