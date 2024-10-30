# app.py
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import json
from pathlib import Path

app = Flask(__name__)

# Load team configuration
def load_team_config():
    with open('config/teams.json', 'r') as f:
        return json.load(f)

# Save auction results to CSV
def save_to_csv(data):
    df = pd.DataFrame([data])
    df.to_csv('auction_results.csv', mode='a', header=not Path('auction_results.csv').exists(), index=False)

# Get team-specific data
def get_team_data(team_name):
    df = pd.read_csv('auction_results.csv')
    team_df = df[df['team'] == team_name]
    return {
        'total_players': len(team_df),
        'indian_players': len(team_df[team_df['nationality'] == 'Indian']),
        'non_indian_players': len(team_df[team_df['nationality'] != 'Indian']),
        'total_spent': team_df['price'].sum(),
        'batters': team_df[team_df['category'] == 'Batter'].to_dict('records'),
        'spin_bowlers': team_df[team_df['category'] == 'Spin Bowler'].to_dict('records'),
        'pace_bowlers': team_df[team_df['category'] == 'Pace Bowler'].to_dict('records'),
        'all_rounders': team_df[team_df['category'] == 'All-Rounder'].to_dict('records'),
        'wicket_keepers': team_df[team_df['category'] == 'Wicket-Keeper'].to_dict('records')
    }

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auctioneer')
def auctioneer():
    teams = load_team_config()
    categories = ['Batter', 'All-Rounder', 'Wicket-Keeper', 'Spin Bowler', 'Pace Bowler']
    return render_template('auctioneer.html', teams=teams, categories=categories)

@app.route('/submit_player', methods=['POST'])
def submit_player():
    data = {
        'team': request.form['team'],
        'player_name': request.form['player_name'],
        'is_indian': request.form['is_indian'] == 'yes',
        'is_capped': request.form['is_capped'] == 'yes',
        'nationality': request.form['nationality'],
        'category': request.form['category'],
        'price': float(request.form['price'])
    }
    
    # Update team purse in config
    teams = load_team_config()
    teams[data['team']]['purse'] -= data['price']
    with open('config/teams.json', 'w') as f:
        json.dump(teams, f, indent=4)
    
    save_to_csv(data)
    return redirect(url_for('auctioneer'))

@app.route('/progress')
def progress():
    teams = load_team_config()
    for team_name in teams:
        df = pd.read_csv('auction_results.csv')
        team_df = df[df['team'] == team_name]
        teams[team_name]['players_bought'] = len(team_df)
    return render_template('progress.html', teams=teams)

@app.route('/team/<team_name>')
def team_breakdown(team_name):
    teams = load_team_config()
    team_info = teams[team_name]
    team_data = get_team_data(team_name)
    return render_template('team_breakdown.html', 
                         team_name=team_name, 
                         team_info=team_info, 
                         team_data=team_data)

@app.route('/download_team/<team_name>')
def download_team(team_name):
    df = pd.read_csv('auction_results.csv')
    team_df = df[df['team'] == team_name]
    output_file = f'downloads/{team_name}_players.csv'
    team_df.to_csv(output_file, index=False)
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)