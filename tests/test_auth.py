def register(client, email='new@usiu.ac.ke', password='secret123'):
    return client.post('/register', data={
        'full_name': 'New Student', 'email': email,
        'reg_no': '654321', 'password': password,
    })


def test_student_can_register_and_log_in(client):
    assert register(client).status_code == 302
    response = client.post('/login', data={
        'email': 'new@usiu.ac.ke', 'password': 'secret123'})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess['role'] == 'student'


def test_wrong_password_is_rejected(client):
    register(client)
    response = client.post('/login', data={
        'email': 'new@usiu.ac.ke', 'password': 'wrong'})
    assert b'Incorrect email or password' in response.data


def test_duplicate_email_is_rejected(client):
    register(client)
    response = register(client)
    assert b'already registered' in response.data


def test_logout_clears_session(client, make_user, login_as):
    user_id, _ = make_user('student')
    login_as(user_id, 'student')
    client.get('/logout')
    with client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_home_redirects_to_login_when_logged_out(client):
    response = client.get('/')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')