import streamlit as st
import matplotlib.pyplot as plt
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
import pandas as pd
from datetime import datetime

def parse_teams(matchup):
   
    if not isinstance(matchup, str):
        return "Inconnu", "Inconnu"
    if " vs. " in matchup:
        home, away = matchup.split(" vs. ")
    elif "@" in matchup:
        away, home = matchup.split(" @ ")
    else:
        return "Inconnu", "Inconnu"
    return home.strip(), away.strip()

def get_detailed_game_stats(game_id):
    
    try:
        boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        return boxscore.get_dict()
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques du match {game_id}: {e}")
        return None

def extract_game_summary(game_details, home_team, away_team):
    
    try:
        player_stats = None
        team_stats = None
        for rs in game_details['resultSets']:
            if rs['name'] == 'PlayerStats':
                player_stats = rs
            elif rs['name'] == 'TeamStats':
                team_stats = rs

        if not player_stats or not team_stats:
            return None

        player_headers = player_stats['headers']
        team_headers = team_stats['headers']
        player_rows = player_stats['rowSet']
        team_rows = team_stats['rowSet']

        team_id_to_name = {}
        for row in team_rows:
            team_id = row[team_headers.index("TEAM_ID")]
            team_abbrev = row[team_headers.index("TEAM_ABBREVIATION")]
            team_name = home_team if team_abbrev == home_team else away_team
            team_id_to_name[team_id] = team_name

        # Déterminer le gagnant
        scores = {
            team_rows[0][team_headers.index("TEAM_ABBREVIATION")]: team_rows[0][team_headers.index("PTS")],
            team_rows[1][team_headers.index("TEAM_ABBREVIATION")]: team_rows[1][team_headers.index("PTS")]
        }
        winner = max(scores, key=scores.get)

        # Trouver les leaders
        team_leaders = {}
        for row in player_rows:
            team_id = row[player_headers.index("TEAM_ID")]
            player = row[player_headers.index("PLAYER_NAME")]
            pts = row[player_headers.index("PTS")]
            reb = row[player_headers.index("REB")]
            ast = row[player_headers.index("AST")]

            if team_id not in team_leaders:
                team_leaders[team_id] = {"PTS": (player, pts), "REB": (player, reb), "AST": (player, ast)}
            else:
                if pts is not None and pts > team_leaders[team_id]["PTS"][1]:
                    team_leaders[team_id]["PTS"] = (player, pts)
                if reb is not None and reb > team_leaders[team_id]["REB"][1]:
                    team_leaders[team_id]["REB"] = (player, reb)
                if ast is not None and ast > team_leaders[team_id]["AST"][1]:
                    team_leaders[team_id]["AST"] = (player, ast)

        # Remplacer team_id par le nom d'équipe
        leaders_named = {
            team_id_to_name[team_id]: stats
            for team_id, stats in team_leaders.items()
        }

        return {
            "home_team": home_team,
            "away_team": away_team,
            "winner": winner,
            "leaders": leaders_named
        }
    except Exception as e:
        print(f"Erreur lors de l'extraction du résumé : {e}")
        return None

def process_games_by_date():
    """
    Récupère tous les matchs pour une date donnée, et extrait les résumés de ces matchs.
    """
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2024-25')
    all_games = gamefinder.get_data_frames()[0]

    date = input("Entrez la date des matchs NBA (YYYY-MM-DD) : ")

    # Filtrer les matchs pour la date spécifiée
    unique_games = all_games.drop_duplicates(subset="GAME_ID", keep="first")
    games_on_date = unique_games[unique_games['GAME_DATE'] == date]

    # Extraire les équipes à domicile et à l'extérieur pour chaque match
    games_on_date["HOME_TEAM_ABBREVIATION"], games_on_date["AWAY_TEAM_ABBREVIATION"] = zip(
        *games_on_date["MATCHUP"].apply(parse_teams)
    )

    summaries = []

    for _, row in games_on_date.iterrows():
        game_id = row["GAME_ID"]
        home_team = row["HOME_TEAM_ABBREVIATION"]
        away_team = row["AWAY_TEAM_ABBREVIATION"]

        game_data = get_detailed_game_stats(game_id)

        if game_data:
            summary = extract_game_summary(game_data, home_team, away_team)
            if summary:
                summaries.append(summary)

def plot_top_players_by_stat(summaries, stat="PTS", top_n=10):
    players_stat = []

    for game in summaries:
        for team, stats in game["leaders"].items():
            player, value = stats[stat]
            if player and value is not None:
                players_stat.append((player, value))

    top_players = sorted(players_stat, key=lambda x: x[1], reverse=True)[:top_n]
    players = [p[0] for p in top_players]
    values = [p[1] for p in top_players]

    title_map = {"PTS": "Top scoreurs du jour", "REB": "Top rebondeurs du jour", "AST": "Top passeurs du jour"}

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(players, values, color="mediumseagreen")
    ax.set_xlabel(stat)
    ax.set_title(title_map[stat])
    ax.invert_yaxis()

    for bar in bars:
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.0f}", va='center')

    st.pyplot(fig)
def get_summaries_for_date(date):
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2024-25')
    all_games = gamefinder.get_data_frames()[0]

    unique_games = all_games.drop_duplicates(subset="GAME_ID", keep="first")
    games_on_date = unique_games[unique_games['GAME_DATE'] == date]

    if games_on_date.empty:
        st.warning(f"Aucun match NBA trouvé pour le {date}.")
        return []

    games_on_date["HOME_TEAM_ABBREVIATION"], games_on_date["AWAY_TEAM_ABBREVIATION"] = zip(
        *games_on_date["MATCHUP"].apply(parse_teams)
    )

    summaries = []
    for _, row in games_on_date.iterrows():
        ...

    for _, row in games_on_date.iterrows():
        game_id = row["GAME_ID"]
        home_team = row["HOME_TEAM_ABBREVIATION"]
        away_team = row["AWAY_TEAM_ABBREVIATION"]

        game_data = get_detailed_game_stats(game_id)
        if game_data:
            summary = extract_game_summary(game_data, home_team, away_team)
            if summary:
                summaries.append(summary)
    return summaries

def generate_daily_summary(summaries):
    
    summary_text = "## 🏀 Résumé stylisé des matchs NBA\n"

    for game in summaries:
        home = game['home_team']
        away = game['away_team']
        winner = game['winner']
        leaders = game['leaders']

        # Petite touche narrative
        phrase = f"{winner} a dominé {home if winner == away else away} sur le parquet.\n"
        summary_text += f"\n- {phrase}"

        for team_name, stats in leaders.items():
            star = stats['PTS'][0]
            pts = stats['PTS'][1]
            reb = stats['REB'][1]
            ast = stats['AST'][1]

            summary_text += f"  \n   🔹 {team_name} : **{star}** a brillé avec {pts} pts, {reb} rebonds et {ast} passes."

        summary_text += "\n"

    return summary_text

def player_of_the_day(summaries):
   
    max_pts = 0
    player_name = ""
    
    for game in summaries:
        for team_name, stats in game['leaders'].items():
            star = stats['PTS'][0]
            pts = stats['PTS'][1]

            if pts > max_pts:
                max_pts = pts
                player_name = star

    return player_name, max_pts
# Interface Streamlit
st.title("📊 Résumés & Top Performeurs NBA")



date_input = st.date_input("Choisis une date de match :", value=datetime.today())
if st.button("Afficher le résumé du jour"):
    formatted_date = date_input.strftime("%Y-%m-%d")
    summaries = get_summaries_for_date(formatted_date)
    
    if summaries:
    # Générer le résumé stylisé
        st.markdown(generate_daily_summary(summaries))

    # Trouver le joueur du jour
        player, points = player_of_the_day(summaries)
        st.markdown(f"## 🌟 Joueur du jour : {player} avec {points} points !")
    else:
        st.warning("Aucun match trouvé pour cette date.")
stat_choice = st.selectbox("Quelle statistique veux-tu visualiser ?", ("PTS", "REB", "AST"))

# Chargement des données




if st.button("Afficher les meilleurs joueurs"):
    formatted_date = date_input.strftime("%Y-%m-%d")
    summaries = get_summaries_for_date(formatted_date)
    if summaries:
        plot_top_players_by_stat(summaries, stat=stat_choice, top_n=10)
    else:
        st.warning("Aucun match trouvé pour cette date.")



    