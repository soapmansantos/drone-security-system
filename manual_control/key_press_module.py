import sys, pygame

def init(screen):
    #creates pygame window to get key_presses
    pygame.init()
    if screen != None:
        display = screen
    else:
        display = pygame.display.set_mode((400, 400))


def key_press(k):
    """
    Returns True if the key specified in the
    input ('k') is pressed, if not, returns False
    """
    ans = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    key_inp = pygame.key.get_pressed()
    if key_inp[getattr(pygame, "K_{}".format(k))]:
        ans = True
    pygame.display.update()

    return ans

def main(controls):
    #given a set of controls to control the drone,
    #it returns when a key of those keys is being pressed
    return [[key_press(i) for i in x] for x in controls]

def exit(key):
    exit = False
    init()
    if key_press(key):
        exit = True

    return exit

if __name__ == "__main__":
    init()
    while True:
        main([["a", "d"], ["w", "s"]])