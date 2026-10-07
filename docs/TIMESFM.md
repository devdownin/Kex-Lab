# Démonstration TimesFM SHADOW de bout en bout

Ce profil optionnel relie du trafic Kafka réel à une métrique de retard temporel, au journal
PostgreSQL, à une prévision TimesFM CPU puis à un processus Kex. Il crée uniquement les ressources
et associations dédiées au laboratoire. Il ne demande aucune activation ACTIVE et n’envoie pas
automatiquement de conversation au LLM.

Le profil reconstruit KafkaExplorer et Kex-agent-ai depuis les SHA exacts de
[`scenarios/timesfm/env.example`](../scenarios/timesfm/env.example), car les images du manifeste
standard du Lab précèdent cette intégration. Le service Python est construit depuis ce même
KafkaExplorer et conserve son modèle/révision/checksum épinglés. Le profil Docker Hub et les
scénarios existants restent utilisables indépendamment.

## Préparer les ressources

Prérequis : Docker Compose avec BuildKit, Git, Python 3, accès aux sources, registres, dépendances
et au téléchargement initial du modèle. Le service TimesFM a un plafond de 4 CPU et 8 Gio ; prévoir
aussi de la mémoire pour Kafka, les deux applications Java, les builds et PostgreSQL. Les budgets
ne constituent pas un benchmark de votre machine. Première construction et téléchargement peuvent
prendre plusieurs minutes ; les poids et données persistent dans des volumes.

Préparer le `.env` standard du Lab avec `KEX_AGENT_API_KEY` et `EXPLORER_MCP_AUTH_TOKEN`.
Conserver les ports standard ou les modifier dans ce fichier. Le projet Compose est isolé sous
`kex-lab-timesfm`, mais utilise les mêmes ports hôte : arrêter une autre stack qui les occupe.
La clé d’agent du scénario doit avoir le rôle ADMIN. Pour une éventuelle conversation ensuite,
configurer le fournisseur LLM comme dans le Lab standard.

```sh
sh scripts/timesfm.sh prepare
sh scripts/timesfm.sh up
set -a
. ./.env
. ./.env.timesfm
set +a
python3 scripts/timesfm-demo.py enroll
sh scripts/timesfm.sh reload
python3 scripts/timesfm-demo.py run --seconds 900
```

`prepare` génère des secrets distincts pour le modèle et PostgreSQL dans `.env.timesfm`
(mode 0600), récupère les révisions exactes et prépare un pilote désactivé. Il refuse de remplacer
un checkout existant modifié ou d’une autre révision. Ne pas publier `.env.timesfm` ni `.timesfm/`.
Il ne faut pas superposer ce profil au fichier `compose.operational-reviews.yml`, qui a sa propre
configuration MCP et son propre parcours ; utiliser les deux démonstrations séparément.

## Ce que le scénario réalise

1. L’initialisation standard crée et alimente le topic déclaré par `KEX_LAB_TOPIC`.
2. `enroll` initialise les offsets du **groupe inactif dédié** `kex-lab-timesfm-worker` au début
   de chaque partition du broker du scénario. Ce groupe reste volontairement sans consommation :
   le retard temporel augmente avec l’âge des messages. Ce geste n’est pas une action de correction
   à appliquer sur un groupe de production.
3. Il crée la métrique dédiée `kex-lab-timesfm-lag`, de type GAUGE et template
   `CONSUMER_TIME_LAG`/MAX, puis collecte dix observations par l’API de refresh réelle.
4. Il lit la dernière observation du journal PostgreSQL et exige une identité de série et une
   version de définition réelles, l’unité `milliseconds`, le composant `value`, le cluster du Lab
   et une qualité source `OBSERVED`. Les lectures partielles ou non vérifiées sont refusées.
5. Il écrit une configuration locale opt-in : environnement `lab`, source topic/groupe exacts,
   cadence 1 s, 512 points, transformation GAUGE_LAST, horizon 60 points et pilote à 1 minute.
   `reload` recharge KafkaExplorer avec cette déclaration et reconnecte l’agent MCP ; aucune
   série n’est inventée.
6. `run` injecte du trafic et rafraîchit la métrique environ deux fois par seconde. Après neuf
   minutes, il vérifie les résultats persistés via les API Kex. Il exige une couverture complète,
   un résultat READY/TIMESFM/SHADOW, des quantiles finis et une échéance future. Un repli ne suffit
   pas à faire réussir cette démonstration du modèle.
7. Il crée le processus dédié si nécessaire, enregistre l’association exacte et vérifie que
   l’aperçu de sa fiche est disponible. Il conserve la preuve datée dans `.timesfm/result.json`.

Les 512 buckets sont observés dans le temps réel. Compter au minimum environ neuf minutes après
le redémarrage, davantage pour le calcul CPU et la prochaine passe du pilote. La borne de 900 s
peut échouer sur une machine lente ; augmenter `--seconds` jusqu’à 3600 et inspecter les diagnostics.
Aucun point n’est antidaté, importé ou remplacé par une valeur fabriquée.

Les seuils de dépassement ne sont pas configurés dans ce scénario initial : l’absence de risque
rendu ne garantit pas l’absence de risque. La qualité réalisée peut rester non mesurée tant que
les prévisions n’ont pas atteint leur échéance et que le pilote n’a pas évalué assez de points.
L’état SHADOW n’est ni une activation ni une garantie de qualité. Les résultats peuvent expirer
quand la collecte s’arrête ; relancer `run` permet de continuer à produire et collecter.

## Vérification dans la console

Ouvrir Kex sur le port configuré, saisir la clé, puis **Pilotage → Prévisions** : choisir `lab`
et la série annoncée par `.timesfm/result.json`. Vérifier les dates, la stratégie, le mode SHADOW,
l’historique et la qualité. Le panneau des ressources doit identifier le topic, le groupe dédié
et le processus **Commandes — démonstration TimesFM**.

Dans sa fiche processus, vérifier l’aperçu daté et **Associer une prévision**. Un retrait puis un
nouvel ajout doit persister sans redémarrage. Dans le wizard, vérifier le diagnostic des cinq
outils et la sélection de cette série. Pour la conversation, cliquer **Analyser avec l’agent**,
relire le brouillon puis l’envoyer explicitement. Attendre constat actuel, prévision, qualité,
limites et vérifications ; ne pas confondre retard mesuré et cause métier.

```sh
python3 scripts/timesfm-demo.py check
sh scripts/timesfm.sh status
sh scripts/timesfm.sh stop
```

`check` vérifie un résultat courant et réenregistre de façon idempotente l’association du
processus dédié. `stop` conserve les volumes et preuves ; aucune suppression de données n’est
incluse dans le parcours. Pour contrôler le temps d’acquisition, relancer la collecte avant
`check` si le dernier horizon a expiré.

## Validation et limites

La CI valide le Compose, la syntaxe et les frontières du scénario (provenance inadmissible,
SHADOW expiré, repli, erreur de couverture, persistance de la paire exacte). Les tests de contrat
utilisent un serveur HTTP contrôlé ; ils ne constituent pas une exécution du modèle. La commande
`run` est la vérification réelle Kafka/PostgreSQL/TimesFM/Kex et doit être exécutée sur une machine
avec Docker et les ressources indiquées. Ce scénario de retard temporel régulier valide le
raccordement ; il ne démontre pas la pertinence du modèle pour un incident métier.
