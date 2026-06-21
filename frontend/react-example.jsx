/**
 * VigScript React Component Example
 *
 * Install dependencies:
 * npm install axios
 *
 * Usage:
 * import BettingCalculator from './BettingCalculator';
 */

import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export function BettingCalculator() {
    const [winProb, setWinProb] = useState(55);
    const [odds, setOdds] = useState(2.0);
    const [amount, setAmount] = useState(100);
    const [bankroll, setBankroll] = useState(1000);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);

    const analyzeBet = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await axios.post(`${API_URL}/analyze/bet`, {
                amount,
                odds,
                win_probability: winProb / 100,
                bankroll
            });

            setResults(response.data);
        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing bet');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <h1 style={styles.title}>Betting Calculator</h1>

            <form onSubmit={analyzeBet} style={styles.form}>
                <div style={styles.formGroup}>
                    <label>Win Probability (%)</label>
                    <input
                        type="number"
                        value={winProb}
                        onChange={(e) => setWinProb(e.target.value)}
                        style={styles.input}
                        min="0"
                        max="100"
                        step="0.1"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>Decimal Odds</label>
                    <input
                        type="number"
                        value={odds}
                        onChange={(e) => setOdds(e.target.value)}
                        style={styles.input}
                        min="1"
                        step="0.01"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>Bet Amount ($)</label>
                    <input
                        type="number"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        style={styles.input}
                        min="0"
                        step="0.01"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>Bankroll ($)</label>
                    <input
                        type="number"
                        value={bankroll}
                        onChange={(e) => setBankroll(e.target.value)}
                        style={styles.input}
                        min="0"
                        step="0.01"
                    />
                </div>

                <button type="submit" style={styles.button} disabled={loading}>
                    {loading ? 'Calculating...' : 'Analyze Bet'}
                </button>
            </form>

            {results && (
                <div style={styles.results}>
                    <h2>Results</h2>
                    <div style={styles.resultItem}>
                        <span>Kelly Criterion:</span>
                        <strong>{results.metrics.kelly_percentage}</strong>
                    </div>
                    <div style={styles.resultItem}>
                        <span>Expected Value:</span>
                        <strong>{results.metrics.ev_formatted}</strong>
                    </div>
                    <div style={styles.resultItem}>
                        <span>Edge:</span>
                        <strong>{results.metrics.edge_percentage}</strong>
                    </div>
                    <div style={styles.resultItem}>
                        <span>ROI:</span>
                        <strong>{results.metrics.roi_percentage}</strong>
                    </div>
                    {results.recommended_bet && (
                        <div style={styles.resultItem}>
                            <span>Recommended Bet:</span>
                            <strong>${results.recommended_bet.toFixed(2)}</strong>
                        </div>
                    )}
                    <div style={{
                        ...styles.recommendation,
                        backgroundColor: results.recommendation === 'STRONG BET' ? '#d4edda' :
                                       results.recommendation.includes('VALUE') ? '#fff3cd' : '#f8d7da'
                    }}>
                        {results.recommendation}
                    </div>
                </div>
            )}
        </div>
    );
}

export function NBAPredictor() {
    const [teamOff, setTeamOff] = useState(115);
    const [teamDef, setTeamDef] = useState(108);
    const [oppOff, setOppOff] = useState(110);
    const [oppDef, setOppDef] = useState(109);
    const [home, setHome] = useState(true);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const predict = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await axios.post(`${API_URL}/predict/nba/quick`, {
                team_off_rtg: teamOff,
                team_def_rtg: teamDef,
                opp_off_rtg: oppOff,
                opp_def_rtg: oppDef,
                home
            });

            setResult(response.data);
        } catch (error) {
            console.error('Error:', error);
            alert('Error making prediction');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <h1 style={styles.title}>NBA Predictor</h1>

            <form onSubmit={predict} style={styles.form}>
                <div style={styles.formGroup}>
                    <label>Team Offensive Rating</label>
                    <input
                        type="number"
                        value={teamOff}
                        onChange={(e) => setTeamOff(e.target.value)}
                        style={styles.input}
                        step="0.1"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>Team Defensive Rating</label>
                    <input
                        type="number"
                        value={teamDef}
                        onChange={(e) => setTeamDef(e.target.value)}
                        style={styles.input}
                        step="0.1"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>Opponent Offensive Rating</label>
                    <input
                        type="number"
                        value={oppOff}
                        onChange={(e) => setOppOff(e.target.value)}
                        style={styles.input}
                        step="0.1"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>Opponent Defensive Rating</label>
                    <input
                        type="number"
                        value={oppDef}
                        onChange={(e) => setOppDef(e.target.value)}
                        style={styles.input}
                        step="0.1"
                    />
                </div>

                <div style={styles.formGroup}>
                    <label>
                        <input
                            type="checkbox"
                            checked={home}
                            onChange={(e) => setHome(e.target.checked)}
                        />
                        {' '}Home Team
                    </label>
                </div>

                <button type="submit" style={styles.button} disabled={loading}>
                    {loading ? 'Predicting...' : 'Predict Winner'}
                </button>
            </form>

            {result && (
                <div style={styles.results}>
                    <h2>Prediction</h2>
                    <div style={styles.resultItem}>
                        <span>Win Probability:</span>
                        <strong style={{ fontSize: '24px', color: '#667eea' }}>
                            {result.win_percentage}
                        </strong>
                    </div>
                </div>
            )}
        </div>
    );
}

export function PerformanceTracker() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);

    const loadStats = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/performance`);
            setStats(response.data);
        } catch (error) {
            console.error('Error:', error);
            alert('Error loading stats');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            <h1 style={styles.title}>Performance Tracker</h1>

            <button onClick={loadStats} style={styles.button} disabled={loading}>
                {loading ? 'Loading...' : 'Load Performance'}
            </button>

            {stats && (
                <div style={styles.results}>
                    <h2>Statistics</h2>
                    <div style={styles.resultItem}>
                        <span>Total Bets:</span>
                        <strong>{stats.total_bets}</strong>
                    </div>
                    <div style={styles.resultItem}>
                        <span>Win Rate:</span>
                        <strong>{(stats.win_rate * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={styles.resultItem}>
                        <span>Total Profit:</span>
                        <strong style={{ color: stats.total_profit >= 0 ? 'green' : 'red' }}>
                            ${stats.total_profit.toFixed(2)}
                        </strong>
                    </div>
                    <div style={styles.resultItem}>
                        <span>ROI:</span>
                        <strong style={{ color: stats.roi >= 0 ? 'green' : 'red' }}>
                            {(stats.roi * 100).toFixed(2)}%
                        </strong>
                    </div>
                </div>
            )}
        </div>
    );
}

// WebSocket Hook for Real-time Updates
export function useWebSocket() {
    const [data, setData] = useState(null);
    const [connected, setConnected] = useState(false);

    React.useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws');

        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            setData(message);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setConnected(false);
        };

        return () => ws.close();
    }, []);

    return { data, connected };
}

// Styles
const styles = {
    container: {
        maxWidth: '600px',
        margin: '0 auto',
        padding: '20px',
    },
    title: {
        textAlign: 'center',
        color: '#333',
        marginBottom: '20px',
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '15px',
    },
    formGroup: {
        display: 'flex',
        flexDirection: 'column',
    },
    input: {
        padding: '10px',
        borderRadius: '5px',
        border: '1px solid #ddd',
        fontSize: '16px',
    },
    button: {
        padding: '15px',
        backgroundColor: '#667eea',
        color: 'white',
        border: 'none',
        borderRadius: '5px',
        fontSize: '16px',
        fontWeight: 'bold',
        cursor: 'pointer',
    },
    results: {
        marginTop: '20px',
        padding: '20px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
    },
    resultItem: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '10px 0',
        borderBottom: '1px solid #e0e0e0',
    },
    recommendation: {
        marginTop: '15px',
        padding: '15px',
        borderRadius: '8px',
        textAlign: 'center',
        fontWeight: 'bold',
    },
};

export default BettingCalculator;
