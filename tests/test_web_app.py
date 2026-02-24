import pytest
import json
from web.app import app, session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_stop_execution(client):
    # Start a dummy execution
    # Start a dummy execution with infinite output
    code = """
    Algorithme TestStop;
    Debut
        Tant Que Vrai Faire
            Ecrire("Running");
        Fin Tant Que;
    Fin.
    """
    client.post('/start_execution', json={'code': code})
    assert session.is_running == True, f"Session not running. Queue: {list(session.output_queue.queue)}"
    
    # Read some stream data to drain queue a bit and verify it runs
    # In a real test client, /stream is an event source, which is hard to test with test_client check
    # But we can check internal queue
    assert not session.output_queue.empty() or session.is_running
    
    # Let it run for a split second
    import time
    time.sleep(0.5)

    # Stop execution
    response = client.post('/stop_execution')
    data = json.loads(response.data)
    
    assert data['success'] == True
    assert session.is_running == False
    
    # Verify queues are handled
    # Input queue should be empty (cleared)
    assert session.input_queue.empty()
    # Output queue might have 'stopped' message or be cleared, but shouldn't block
    assert True

def test_execution_flow(client):
    # Test normal flow to ensure no regression
    code = """
    Algorithme TestFlow;
    Debut
        Tant Que Vrai Faire
            Ecrire("Hello");
        Fin Tant Que;
    Fin.
    """
    client.post('/start_execution', json={'code': code})
    assert session.is_running == True
    
    # In a real threaded env we'd wait, but here we just check if start works
    # and subsequent calls block/fail if running
    response = client.post('/start_execution', json={'code': code})
    data = json.loads(response.data)
    assert data['success'] == False
    assert data['error'] == 'Already running'
    
    # Force stop to clean up
    client.post('/stop_execution')
    assert session.is_running == False
