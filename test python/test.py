import mysql.connector
import itertools
import re
connect = mysql.connector.connect(
    user='root',
    password='',
    host='localhost',
    database='testpython'
)
if connect.is_connected():
    print('connected successfully')
    cursor = connect.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS Combinaisons (id INT AUTO_INCREMENT PRIMARY KEY, etapes VARCHAR(255))")

    #Liste des étapes
    etapes = ["1.1", "1.2", "1.3", "2.1", "2.2", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "4.1", "4.2", "4.3", "4.4", "5.1", "5.2", "5.3", "5.4", "5.5", "6.1", "6.2", "6.3", "6.4"]

  # Génération des combinaisons possibles de variables logiques (VRAI/FAUX)
    combinaisons = list(itertools.product([False, True], repeat=len(etapes)))

# Insertion >>"Combinaisons"
    for comb in combinaisons:
        etapes_comb = ",".join([etapes[i] for i in range(len(comb)) if comb[i]])
        cursor.execute("INSERT INTO Combinaisons (etapes) VALUES (%s)", (etapes_comb,))
        connect.commit()
        cursor.execute("SELECT COUNT(*) FROM Combinaisons")
        nombre_lignes_combinaisons = cursor.fetchone()[0]
        print("Nombre de lignes insérées dans la table Combinaisons :", nombre_lignes_combinaisons)
# Création de la table "Regles"
        cursor.execute("CREATE TABLE IF NOT EXISTS Regles (id INT AUTO_INCREMENT PRIMARY KEY, statut_sous_statut VARCHAR(50), regle VARCHAR(255))")

regles = [
     ("Information avant accrochage", "(Rien OR 1.1 OR 1.2 OR 1.1 AND 1.2) AND NOT 1.3 AND NOT 6.4"),
     ("En cours d'accrochage", "1.1 AND 1.2 AND 1.3 AND NOT (2.1 AND ... AND 5.5) AND NOT 6.4"),
     ("En cours d'accrochage > Initialisation du projet d'accrochage", "1.1 AND 1.2 AND 1.3 AND NOT 2.1 ... NOT 5.5 AND NOT 6.4"),
     ("En cours d'accrochage > Accrochage technique", "1.1 AND 1.2 AND 1.3 AND 2.1 AND 2.2 AND NOT  5.5 AND NOT 6.4"),
     ("En cours d'accrochage > Validation de conformité", "1.1 AND 1.2 AND 1.3 AND 2.1 AND 2.2 AND 3.1 AND 3.2 AND 3.3 AND 3.4 AND 3.5 AND NOT  5.5 AND NOT 6.4"),
     ("En cours d'accrochage > Mise en production", "1.1 AND ... AND 4.4 AND NOT 5.1 ... NOT 5.5 AND NOT 6.4"),
     ("En production", "1.1 AND ... AND 3.5 AND 4.1 AND 4.2 AND 5.1 ... AND 5.5 AND NOT 6.4"),
     ("En production - OK", "1.1 AND ... AND 5.5 AND NOT 6.4"),
     ("En production - Adaptations spécifiques", "1.1 AND ... AND 3.5 AND NOT 3.6 AND 4.1 AND ... AND 5.5 AND NOT 6.4"),
     ("En production - Requalification CA", "1.1 AND ... AND 3.5 AND 4.1 AND 4.2 (NOT 4.3 OR NOT 4.4 OR NOT 4.3 AND NOT 4.4) AND 5.1 AND ... AND 5.5 AND NOT 6.4"),
     ("Accrochage stoppé", "6.4")
 ]
#insertion dans le table regle   
for regle in regles:
        cursor.execute("INSERT INTO Regles (statut_sous_statut, regle) VALUES (%s, %s)", (regle[0], regle[1]))
        connect.commit()
        print("insertion s'effectue avec succées")
      
# Création de la table "correspondance_combinaison_regle"
cursor.execute("CREATE TABLE IF NOT EXISTS correspondance_combinaison_regle (id INT AUTO_INCREMENT PRIMARY KEY, combinaison_id INT, regle_id INT)")
print("table regle combinaison")
# Vérification des correspondances "combinaison-regle" et insertion dans la table 
cursor.execute("SELECT * FROM Combinaisons")
combinaisons = cursor.fetchall()
#print(combinaisons)
cursor.execute("SELECT * FROM Regles")
regles = cursor.fetchall()
print(len(etapes))
print(len(combinaisons))
print(regles)
for combinaison_id, combinaison in combinaisons:
    for regle_id, statut_sous_statut, regle in regles:
        regle_modifiee = regle
        for index, etape in enumerate(etapes):
             if index < len(combinaison):
               regle_modifiee = regle_modifiee.replace(str(index + 1), str(combinaison[index]))

               print("regle_modifiee",regle_modifiee)
               test= regle_modifiee.replace('...', 'true')
               test = test.replace('OR', 'or')  
               test = test.replace('AND', 'and')  
               test = test.replace('NOT', 'not') 
               test = test.replace('Rien', 'False') 
            
               print("test",test)
               if eval(test ):
                cursor.execute("INSERT INTO correspondance_combinaison_regle (combinaison_id, regle_id) VALUES (%s, %s)", (combinaison_id, regle_id))
                connect.commit()

    cursor.close()
#close connection 
    connect.close()
else: 
    print(' there is problem')


#les question optionelle:
    
requete1 = """
SELECT combinaisons.*
FROM combinaisons
LEFT JOIN correspondance_combinaison_regle ON combinaisons.id = correspondance_combinaison_regle.id
WHERE correspondance_combinaison_regle.id IS NULL;
"""

# Requête pour identifier les combinaisons qui sont dans plusieurs statuts ou sous-statuts
requete2 = """
SELECT id_combinaison, COUNT(id_combinaison) AS nb_statuts
FROM correspondance_combinaison_regle
GROUP BY id_combinaison
HAVING nb_statuts > 1;
"""

# Requête pour identifier s'il y a une correspondance exacte entre les combinaisons d'un statut et de l'ensemble de ses sous-statuts
requete3 = """
SELECT statut_sous_status, COUNT(DISTINCT id_combinaison) AS nb_combinaisons
FROM regles
INNER JOIN correspondance_combinaison_regle ON regles.id = correspondance_combinaison_regle.id
GROUP BY statut_sous_status
HAVING COUNT(DISTINCT id_combinaison) = (
    SELECT COUNT(DISTINCT id_combinaison)
    FROM Regles
    WHERE statut_sous_status = 'En cours d\'accrochage' OR Statut = 'En production'
);
"""

