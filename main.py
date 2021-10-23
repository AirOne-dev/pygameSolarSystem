import requests, json, pygame, io, os, math, random

# échelle de la simulation par rapport à la vrai vie
scale = 10/100000

pygame.init()

screenW, screenH = 768,768
screen = pygame.display.set_mode((screenW, screenH))
font = pygame.font.SysFont('sans-serif', 24)
clock = pygame.time.Clock()
play = True
planetList = []
originalPlanetList = []
sun = None

# Cette definition de classe est sympa car elle nous
# permet de faire mouse.pos.x, ou mouse.click.left, ...
class Mouse:
    class Pos:
        def __init__(self):
            self.x = screenW/2
            self.y = screenH/2

    class Click:
        def __init__(self):
            self.left = False
            self.right = False

    def __init__(self):
        self.pos = self.Pos()
        self.click = self.Click()
        self.dx = 1
        self.dy = 1

mouse = Mouse()

class Planet:
    def __init__(self, name, radius, image, distanceToSun, order, revolution = 0, nbSatelites = 0):
        
        # stock les valeurs originales car on a besoin d'elles
        # si on veut resize
        self.oRadius = radius
        self.oDistanceToSun = distanceToSun
        self.oImage = image

        self.name = name
        print(self.name + ': ' + str(self.oDistanceToSun))
        self.order = order
        self.scale = scale
        self.revolution = revolution
        self.theta = random.random()*math.pi*2
        self.satelites = []
        
        self.updateScale()
        self.txt = font.render(str(self.name), True, (255, 255, 255))

        for i in range(0, int(nbSatelites)):
            s = self.Satelite(
                self.posX,
                self.posY,
                self.radius * 1.2,
                self.radius / 10
            )
            self.satelites.append(s)
        
    # Calcule les tailles / positions en fonction de la variable "scale"
    def updateScale(self):
        # nb : les tailles des planètes ne correspondent pas totalement à la réalité
        # car sinon il faudrait trop dézoomer pour voir toute la simulation

        # mais les vrai tailles / distances sont utilisées quand même dans
        # les calculs, afin de se rapprocher un peu de la réalité

        self.radius = self.oRadius * self.scale * 7
        if self.oRadius < 7000:
            self.radius = self.radius * 4
        elif self.oRadius > 100000:
            self.radius = self.radius / 8
            
        
        self.distanceToSun = (self.order * 50 + self.oDistanceToSun / 70000000) * self.scale * 15000
        self.image = pygame.transform.scale(self.oImage, (int(self.radius*2), int(self.radius*2)))
        self.posX, self.posY = mouse.pos.x, mouse.pos.y

        for satelite in self.satelites:
            satelite.distanceToPlanet = satelite.rDistance * self.radius * 1.1
            satelite.radius = satelite.rRadius * self.scale * 20000


    # Affiche sur une "surface" donnée la planète à la bonne taille / position
    def display(self, surface):
        surface.blit(self.image, (self.posX - self.radius, self.posY - self.radius))
        surface.blit(self.txt, (self.posX - self.txt.get_width() / 2, self.posY + self.radius + 5))

    # Une planète peut avoir des satelites, c'est pourquoi la classe
    # Satelite est défini dans la classe Planete
    class Satelite:
        def __init__(self, posX, posY, distanceToPlanet, radius):
            self.posX = posX
            self.posY = posY
            self.rDistance = random.randint(1, 125) / 100
            self.rRadius = random.randint(25, 125) / 100
            self.distanceToPlanet = distanceToPlanet * self.rDistance
            self.rotateSpeed = self.distanceToPlanet * self.rRadius / 100
            self.radius = self.rRadius
            self.theta = random.random()*math.pi*2

# Si le dossier 'tmp' n'éxiste pas en local, alors
# on le créer
if not os.path.exists('./tmp'):
    os.makedirs('./tmp')

# Si les données de l'api ne sont pas téléchargées en local
# alors on les télécharges
if not os.path.isfile('./tmp/data.json'):
    solarySystemApi = "https://www.datastro.eu/api/records/1.0/search/?dataset=donnees-systeme-solaire-solar-system-data&q=&sort=-distance_moyenne_average_distance_x10_6_km&facet=planete_planet&facet=distance_moyenne_average_distance_x10_6_km&facet=diametre_diameter_km&facet=gravite_gravity_m_s2"
    r = requests.get(solarySystemApi)
    file = open('./tmp/data.json', "wb")
    file.write(r.content)
    file.close()

# On met en mémoire les données sauvegardées de l'api
file = open('./tmp/data.json', "r")
r = json.loads(file.read())
file.close()



for planet in r["records"]:
    planet = planet["fields"]

    # Dans certains cas, des champs de l'api n'éxistent pas pour certaines planètes
    # On teste ici s'ils existent, si ce n'est pas le cas on défini le champ à zéro
    distanceToSun = 0 if planet.get("distance_moyenne_average_distance_x10_6_km") == None else planet["distance_moyenne_average_distance_x10_6_km"] * 10000000
    revolution = 0 if planet.get("periode_de_revolution_an_orbital_period_year") == None else planet["periode_de_revolution_an_orbital_period_year"]
    satelites = 0 if planet.get("nombre_de_satellites_number_of_satellites") == None else planet["nombre_de_satellites_number_of_satellites"]
    
    imgLocalPath = './tmp/' + planet["image"]["id"] + '.jpeg'
    img = None

    # Si l'image de la planète existe en local, ça la charge en mémoire
    if os.path.isfile(imgLocalPath):
        img = open(imgLocalPath)

    # Sinon on télécharge l'image de celle-cic, et la charge en mémoire
    else:
        imgR = requests.get("https://www.datastro.eu/explore/dataset/donnees-systeme-solaire-solar-system-data/files/" + planet["image"]["id"] + "/300/")

        file = open(imgLocalPath, "wb")
        file.write(imgR.content)
        file.close();
        img = io.BytesIO(imgR.content)
    
    
    # On instancie une nouvelle planète à partir des infos chargées
    # depuis l'api
    p = Planet(
        planet["planete_planet"],
        planet["diametre_diameter_km"]  / 2,
        pygame.image.load(img),
        distanceToSun,
        planet["ordre_order"],
        revolution,
        satelites
    )

    # Si la distance avec le soleil est égale à zéro, alors on dit que la planète
    # est le soleil, et on le met à part, car il s'agit de la planète centrale de
    # cette simulation
    if distanceToSun == 0:
        sun = p
    else :
        planetList.append(p)


originalPlanetList = planetList.copy()
randomPlanetNameList = ["Aaron", "Adonis", "Ajax", "Albert", "Alceste", "Alcibiade", "Amphitryon", "Anchise", "Antigone", "Apollon", "Archimède", "Arès", "Ariarathe", "Aristide", "Aléxios", "Aristo", "Aristote", "Athos", "Balusse", "Belphegor", "Cléon", "Cyriacus", "Cyrille", "Caïus", "Cronos", "Créon", "Copreus", "Démophon", "Daphnis", "Daméas", "Dédale", "Deucalion", "Erwan", "Énée", "Endymion", "Epiméthée", "Éphise", "Éros", "Eschyle", "Ésope", "Eusèbe", "Exupère", "Eurysthée", "Hadès", "Hector", "Héphaistion", "Hermès", "Hercule", "Héraclès", "Hélénos", "Homère", "Horace", "Hypérion", "Hyacinthe", "Hémon", "Isaac", "Icare", "Iolaos", "Japet", "Joachim", "Luc Damas", "Léonidas", "Lazare", "Laurent", "Léandre", "Marcus", "Nérée", "Néarque", "Nicodème", "Orphée", "Octave", "Ouréa", "Ovide", "Ouranos", "Pamphile", "Pâris", "Philotas", "Patrocle", "Pausianas", "Phinée", "Priam", "Politès", "Polyeucte", "Polyphème", "Procas", "Rémus", "Romulus", "Rufus", "Sabin", "Sophocle", "Thalès", "Télémaque", "Théophile", "Théophraste", "Thibert", "Tibulle", "Timon", "Titus", "Tullia", "Tybalt", "Ulysse", "Xénophon", "Xanthos", "Zénon", "Zeus", "Aphrodite", "Artémis", "Aspasie", "Athéna", "Andromaque", "Andromède", "Ariane", "Antigone", "Aquaria", "Alix", "Bérénice", "Briséis", "Barbarella", "Calliope", "Cassiopée", "Circé", "Clytemnestre", "Clytia", "Cybèle", "Danaé", "Dalia", "Diane", "Didon", "Dione", "Erato", "Eulalie", "Eurus", "Eurydice", "Euterpe", "Etana", "Eugénie", "Fama", "Firmine", "Flava", "Gaïa", "Hécate", "Hécube", "Héra", "Iphigénie", "Ismène",  "Junon", "Jihane", "Léto", "Livia", "Lamia", "Maia", "Médée", "Melpomène", "Macarie", "Néra", "Nyx", "Pandore", "Pasiphaé", "Perséphone", "Phèdre", "Polymnie", "Proserpine", "Psychée", "Pyrrha", "Octavia", "Olympia", "Stratonice", "Silene", "Séléné", "Shéhérazade", "Thalie", "Terpsichore", "Uranie", "Xéna"]
# La liste ci dessus est une liste de prénoms antiques, qui (je trouve)
# inspirent bien des noms de planètes, elle a été récupérée sur 
# https://fr.wikipedia.org/wiki/Liste_de_prénoms_d%27origine_antique

# via un script :

# let nameList = "";
# document.querySelectorAll('.colonnes li').forEach(name => {
#     nameList += '"' + name.innerText + '", ';
# });
# console.log(nameList);

while play:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            play = False

        if event.type == pygame.MOUSEBUTTONDOWN :

            # Si le clique gauche est enfoncé 
            if event.button == 1 :
                mouse.click.left = True
                    
            # Si le clique droit est enfoncé 
            if event.button == 3 :
                mouse.click.right = True
                

        if event.type == pygame.MOUSEBUTTONUP:
            
            # Si on scroll avec la molette
            if event.button == 4 or event.button == 5:
                if event.button == 4:
                    scale += 1/300000
                if event.button == 5:
                    scale -= 1/300000
                    if scale <= 1/300000:
                        scale = 1/300000

                # On change la taille / position des planètes, ce qui
                # donne l'impression de zoomer/dézoomer sur la map
                sun.scale = scale
                sun.updateScale();
                for planet in planetList:
                    planet.scale = scale
                    planet.updateScale();

            # Si le clique gauche est relaché
            if event.button == 1:
                mouse.click.left = False

            # Si le clique droit est relaché
            if event.button == 3:
                mouse.click.right = False

                cursorX = abs(mouse.dx - mouse.pos.x)
                cursorY = abs(mouse.dy - mouse.pos.y)
                action = "add"

                for index, planet in enumerate(planetList):
                    if cursorX > planet.posX-planet.radius and cursorX < (planet.posX + planet.radius * 2):
                        if cursorY > planet.posY-planet.radius and cursorY < (planet.posY + planet.radius * 2):
                            # Si le click est sur la planète, on dit que l'action sera de
                            # supprimer, avec la position de la planète dans le tableau
                            action = "delete-" + str(index)

                action = action.split('-')
                if action[0] == "delete":
                    del planetList[int(action[1])]
                elif action[0] == "add":
                    # Calcul de la distance entre le curseur et le soleil
                    distanceToSun = math.sqrt( math.pow(sun.posX-cursorX, 2) + math.pow(sun.posY-cursorY, 2) ) / scale * 4650
                    
                    # Calcul de l'angle entre le curseur et le soleil (comme
                    # si le curseur etait un point d'un cercle qui a pour
                    # centre le soleil)
                    angle = math.atan2(cursorY - sun.posY ,cursorX - sun.posX)
                    
                    # Prend une planète aléatoire du système solaire généré
                    # au début du programme pour récupérer son image

                    rPos = random.randint(0, len(originalPlanetList)-1)
                    print(originalPlanetList[rPos].oRadius);
                    rPlanet = Planet(
                        randomPlanetNameList[random.randint(0, len(randomPlanetNameList)-1)],
                        random.randint(100, 50000),
                        originalPlanetList[rPos].oImage,
                        distanceToSun,
                        0,
                        distanceToSun/15000000000,
                        random.randint(0, 20),

                    )
                    rPlanet.theta = angle
                    rPlanet.updateScale()
                    planetList.append(rPlanet)
        
        # Si on bouge la souris
        if event.type == pygame.MOUSEMOTION:
            if mouse.click.left == True:
                mouse.pos.x = event.pos[0] + mouse.dx
                mouse.pos.y = event.pos[1] + mouse.dy
            else:
                mouse.dx = mouse.pos.x - event.pos[0]
                mouse.dy = mouse.pos.y - event.pos[1]

            # On déplace toutes les planètes, ce qui
            # donne l'impression de se déplacer dans la map
            sun.posX, sun.posY = mouse.pos.x, mouse.pos.y
            for planet in planetList:
                planet.posX, planet.posY = mouse.pos.x, mouse.pos.y

        # Si on appuie sur Echap, quitte le programme
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                play = False

    # Rempli la fenêtre de noir
    screen.fill((0,0,0))

    # Affiche le soleil
    sun.display(screen)

    # On affiche les trajectoires des planètes,
    # je le fais dans un avant le for pour les planètes afin d'afficher les
    # cercles derrière toutes les planètes
    for planet in planetList:
        pygame.draw.circle(screen,  (50, 50, 50), (sun.posX, sun.posY), planet.distanceToSun, width=1)

    # Calcule l'angle des planetes autour du soleil et les affiches
    for planet in planetList:
        planet.theta += 2 * math.pi / (360 / -1*planet.revolution)
        planet.posX = mouse.pos.x + planet.distanceToSun * math.cos(planet.theta)
        planet.posY = mouse.pos.y + planet.distanceToSun * math.sin(planet.theta)
        
        planet.display(screen)


        # Calcule l'angle des satelites autour de la planete et les affiche
        for satelite in planet.satelites:
            satelite.theta += 2 * math.pi / 360 * satelite.rotateSpeed
            satelite.posX = planet.posX + satelite.distanceToPlanet * math.cos(satelite.theta)
            satelite.posY = planet.posY + satelite.distanceToPlanet * math.sin(satelite.theta)

            pygame.draw.circle(screen,  (255, 255, 255), (satelite.posX, satelite.posY), satelite.radius)

    # Affiche les infos sur les commandes en bas à gauche de l'écran
    text = "[Infos] \n\n - clique droit : ajoute/supprime un satelite \n - clique gauche + souris : se déplacer \n - molette : zoom/dé-zoom"
    textLines = text.split('\n')
    for index, line in enumerate(textLines):
        info = font.render(line, False, (255, 255, 255))
        screen.blit(info, (5, screenH - (info.get_height()*(len(textLines)-index)) - 5))


    clock.tick(60)
    pygame.display.flip()