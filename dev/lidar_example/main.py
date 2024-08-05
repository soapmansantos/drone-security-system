import sensors, env, sys, pygame, math

environment = env.Environment((1200, 600))
environment.original_map = environment.map.copy()

laser = sensors.Sensor(200, environment.original_map, uncertainty=(0.5, 0.01))
environment.map.fill((255, 255, 255))
environment.infomap = environment.map.copy()

while True:
	sensor_on = False

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

		if pygame.mouse.get_focused():
			sensor_on = True
		elif not pygame.mouse.get_focused():
			sensor_on = False

	if sensor_on:
		laser.pos = pygame.mouse.get_pos()
		sensor_data = laser.sense_obstacles()
		environment.data_storage(sensor_data)
		environment.show_sensor_data()

	environment.map.blit(environment.infomap, (0, 0))

	pygame.display.update()