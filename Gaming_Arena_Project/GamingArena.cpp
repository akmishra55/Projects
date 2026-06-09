#include <iostream>
#include <cstdlib>
#include <ctime>
#include <conio.h>
#include <windows.h>
#include <deque>
#include <vector>
#include <cstring>
#include <ctype.h>

using namespace std;
const int ROWS = 20;
const int COLS = 20;

enum Direction
{
    UP,
    DOWN,
    LEFT,
    RIGHT
};

class Fruit
{
private:
    int row;
    int col;

public:
    Fruit()
    {
        row = 0;
        col = 0;
    }
    void generate()
    {
        row = rand() % ROWS;
        col = rand() % COLS;
    }
    int getRow()
    {
        return row;
    }

    int getCol()
    {
        return col;
    }
};

class Snake
{
private:
    int row;
    int col;
    Direction direction;
    int tailRow[ROWS * COLS];
    int tailCol[ROWS * COLS];
    int tailLength;

public:
    Snake()
    {
        row = ROWS / 2;
        col = COLS / 2;
        direction = UP;
        tailLength = 0;
    }
    void changeDirection(Direction newDirection)
    {
        if (direction == UP && newDirection == DOWN || direction == DOWN && newDirection == UP || direction == LEFT && newDirection == RIGHT || direction == RIGHT && newDirection == LEFT)
        {
            return;
        }
        direction = newDirection;
    }
    void move()
    {
        for (int i = tailLength - 1; i > 0; i--)
        {
            tailRow[i] = tailRow[i - 1];
            tailCol[i] = tailCol[i - 1];
        }
        if (tailLength > 0)
        {
            tailRow[0] = row;
            tailCol[0] = col;
        }
        switch (direction)
        {
        case UP:
            row--;
            break;
        case DOWN:
            row++;
            break;
        case LEFT:
            col--;
            break;
        case RIGHT:
            col++;
            break;
        }
        if (row < 0)
        {
            row = ROWS - 1;
        }
        else if (row >= ROWS)
        {
            row = 0;
        }
        if (col < 0)
        {
            col = COLS - 1;
        }
        else if (col >= COLS)
        {
            col = 0;
        }
        for (int i = 0; i < tailLength; i++)
        {
            if (row == tailRow[i] && col == tailCol[i])
            {
                tailLength = 0;
            }
        }
    }
    void eatFruit(Fruit &fruit)
    {
        if (row == fruit.getRow() && col == fruit.getCol())
        {
            tailLength++;
            fruit.generate();
        }
    }

    int getRow()
    {
        return row;
    }

    int getCol()
    {
        return col;
    }

    int getTailLength()
    {
        return tailLength;
    }

    int getTailRow(int index)
    {
        return tailRow[index];
    }

    int getTailCol(int index)
    {
        return tailCol[index];
    }
};

class fruit_and_snake
{
private:
    Snake snake;
    Fruit fruit;

public:
    void play()
    {
        fruit.generate();
        while (true)
        {
            system("cls");
            drawBoard();
            handleInput();
            snake.move();
            snake.eatFruit(fruit);
            if (snake.getTailLength() == ROWS * COLS)
            {
                system("cls");
                cout << "Congratulations! You won!" << endl;
                break;
            }
            for (int i = 0; i < snake.getTailLength(); i++)
            {
                if (snake.getRow() == snake.getTailRow(i) && snake.getCol() == snake.getTailCol(i))
                {
                    system("cls");
                    cout << "Game over!" << endl;
                    return;
                }
            }
            Sleep(100);
        }
    }

private:
    void drawBoard()
    {
        for (int i = 0; i < ROWS; i++)
        {
            for (int j = 0; j < COLS; j++)
            {
                if (i == snake.getRow() && j == snake.getCol())
                {
                    cout << "O";
                }
                else if (i == fruit.getRow() && j == fruit.getCol())
                {
                    cout << "F";
                }
                else
                {
                    bool isTail = false;
                    for (int k = 0; k < snake.getTailLength(); k++)
                    {
                        if (i == snake.getTailRow(k) && j == snake.getTailCol(k))
                        {
                            cout << "o";
                            isTail = true;
                            break;
                        }
                    }
                    if (!isTail)
                    {
                        cout << ".";
                    }
                }
            }
            cout << endl;
        }
    }

    void handleInput()
    {
        if (_kbhit())
        {
            switch (_getch())
            {
            case 'w':
                snake.changeDirection(UP);
                break;
            case 's':
                snake.changeDirection(DOWN);
                break;
            case 'a':
                snake.changeDirection(LEFT);
                break;
            case 'd':
                snake.changeDirection(RIGHT);
                break;
            }
        }
    }
};

class rps
{
private:
    int userScore;
    int computerScore;
    int ties;

public:
    rps()
    {
        userScore = 0;
        computerScore = 0;
        ties = 0;
    }

    void play()
    {

        while (true)
        {
            cout << "Enter your move (1: Rock, 2: Paper, 3: Scissors, 4: Quit): ";
            int userMove;
            cin >> userMove;
            if (userMove < 1 || userMove > 4)
            {
                cout << "Invalid move! Please enter a valid move." << endl;
                continue;
            }
            if (userMove == 4)
            {
                break;
            }

            int computerMove = rand() % 3 + 1; // Generate a random move for the computer

            cout << "You played " << moveToString(userMove) << "." << endl;
            cout << "The computer played " << moveToString(computerMove) << "." << endl;

            int result = getResult(userMove, computerMove);
            if (result == 1)
            {
                cout << "You win!" << endl;
                userScore++;
            }
            else if (result == -1)
            {
                cout << "You lose!" << endl;
                computerScore++;
            }
            else
            {
                cout << "It's a tie!" << endl;
                ties++;
            }

            cout << "Score: You " << userScore << ", Computer " << computerScore << ", Ties " << ties << "." << endl;
        }

        cout << "Final score: You " << userScore << ", Computer " << computerScore << ", Ties " << ties << "." << endl;
    }

private:
    string moveToString(int move)
    {
        switch (move)
        {
        case 1:
            return "Rock";
        case 2:
            return "Paper";
        case 3:
            return "Scissors";
        default:
            return "";
        }
    }

    int getResult(int userMove, int computerMove)
    {
        if (userMove == computerMove)
        {
            return 0;
        }
        else if (userMove == 1 && computerMove == 3)
        {
            return 1;
        }
        else if (userMove == 2 && computerMove == 1)
        {
            return 1;
        }
        else if (userMove == 3 && computerMove == 2)
        {
            return 1;
        }
        else
        {
            return -1;
        }
    }
};

#include <iostream>
#include <conio.h>
#include <windows.h>
#include <fstream>
#include <iomanip>
#include <unistd.h>
#include <cstdlib>
#include <ctime>
#include <bits/stdc++.h>
#include <vector>

using namespace std;

int score_number;

string pressed1_0()
{
    string ans;
    cin >> ans;

    if (ans == "Y")
    {
        return ans;
    }
    else if (ans == "N")
    {
        ans = "THANKS FOR PLAYING";
        return ans;
    }
    else
    {
        ans = "INVALID COMMAND";
        return ans;
    }
}

int count_score(int attempts)
{
    switch (attempts)
    {
    case 1:
        score_number += 60;
        break;
    case 2:
        score_number += 50;
        break;
    case 3:
        score_number += 40;
        break;
    case 4:
        score_number += 30;
        break;
    case 5:
        score_number += 25;
        break;
    case 6:
        score_number += 20;
        break;
    case 7:
        score_number += 15;
        break;
    default:

        cout << "******   ERROR 404 FOUND   *****"
             << "\n";
    }
    return score_number;
}

string login_number()
{
    system("cls");
    cout << "\t\t\t--------------------------------------------------------------------------------\n";
    cout << "\t\t\t                                   WELCOME TO OUR GAME                          \n";
    cout << "\t\t\t--------------------------------------------------------------------------------\n"
         << "\n\n\n";
    cout << "\t\t\t--------------------------------------------------------------------------------\n";
    cout << "\t\t\t                                       MENU                                     \n  ";
    cout << "\t\t\t--------------------------------------------------------------------------------\n"
         << "\n\n\n";
    cout << "                                       ";

    cout << "PRESS 1 TO PLAY OR 0 TO EXIT"
         << "\n\n";
    cout << "                                       ENTER YOUR CHOICE->";
    int c;
    cin >> c;
    cout << "\n";
    string name;

    switch (c)
    {
    case 1:
        cout << "\tPLAYER NAME------->";
        cin >> name;
        return (name);
        break;
    case 0:

        cout << "\t\t\t\t----------------------------------------------------------------\n";
        cout << "\t\t\t\t_________THANKS FOR PLAYING_______";
        cout << "\t\t\t\t----------------------------------------------------------------\n";

        exit(0);
    default:

        cout << "\t\t\t\t----------------------------------------------------------------\n";
        cout << "\t\t\t\t_________INVALID COMMAND________\n\n";
        cout << "\t\t\t\t----------------------------------------------------------------\n";

        cout << "\t\t\t\t----------------------------------------------------------------\n";
        cout << "\t\t\t\t___________TRY AGAIN__________\n\n ";
        cout << "\t\t\t\t----------------------------------------------------------------\n";

        login_number();
    }
}

void casino()
{
    system("cls");
labell:
    int n;
    cout << "\n\n\n\nNUMBER OF PLAYER PLAYING THE GAME->";
    cin >> n;

    while (n--)
    {
        string name;
        name = login_number();
        srand(time(0)); // Seed the random number generator
        int score_number;
        score_number = 0;
        const int minNumber = 1;
        const int maxNumber = 100;
        const int maxAttempts = 7; // Maximum number of attempts allowed

        int secretNumber = rand() % (maxNumber - minNumber + 1) + minNumber;
        int guess;
        int attempts = 0;
        bool correctGuess = false;
        cout << "\n\n                       "
             << " _____________________________ INTRODUCTION _____________________________\n";
        cout << "                      "
             << " |                                                                       |\n";
        cout << "                      "
             << " |     	           Welcome to the Number Guessing Game!    	    	    |\n";
        cout << "                      "
             << " |       I'm thinking of a number between " << minNumber << " and " << maxNumber << " .|\n";
        cout << "                      "
             << " |       You have " << maxAttempts << " attempts to guess it            .|\n";
        cout << "                      "
             << " |_______________________________________________________________________|\n\n\n\n";

        while (attempts < maxAttempts && !correctGuess)
        {
            cout << "Attempt #" << attempts + 1 << ": Enter your guess: ";
            cin >> guess;
            attempts++;

            if (guess == secretNumber)
            {
                cout << "Congratulations! You guessed the correct number (" << secretNumber << ") in " << attempts << " attempts.\n";
                correctGuess = true;

                score_number = count_score(attempts);

                sleep(2);
            }

            else if (guess < secretNumber)
            {
                cout << "Too low. Try again!\n";
            }

            else
            {
                cout << "Too high. Try again!\n";
            }
        }

        if (!correctGuess)
        {
            cout << "Sorry, you've run out of attempts. The correct number was: " << secretNumber << endl;
            score_number = 0;
            sleep(2);
        }

        system("cls");
    }
    cout << "\n\n\n\n                    ";

    cout << "********  PLAY AGAIN ***********\n\n\n";

    cout << "                    ";

    cout << "*** YES ************ NO *****\n\n\n\n\n";
    cout << "                          ";
    cout << "\n\n\t\t\t\t\t---------------- INSTRUCTION --------------\n\n";

    cout << "\t\t\t\t\t---------- PRESS 'Y' FOR YES AND 'N'  FOR NO ----------";

    string pressed1;
    pressed1 = pressed1_0();

    if (pressed1 == "Y")
    {
        goto labell;
    }

    else
    {
        cout << "\n\n\n\n\n---------------------------------------------------------------\n";
        cout << "                      " << pressed1 << "                       \n";
        cout << "---------------------------------------------------------------\n";
    }
}

enum edir
{
    STOP = 0,
    lEFT = 1,
    UPLEFT = 2,
    DOWNLEFT = 3,
    rIGHT = 4,
    UPRIGHT = 5,
    DOWNRIGHT = 6
};
class ball
{
private:
    int x, y;
    int start_x, start_y;
    edir direction;

public:
    ball(int posx, int posy)
    {
        start_x = posx;
        start_y = posy;
        x = posx;
        y = posy;
        direction = STOP;
    }

    void reset()
    {
        x = start_x;
        y = start_y;
        direction = STOP;
    }

    void changedir(edir d)
    {
        direction = d;
    }

    void random_dir()
    {
        direction = (edir)((rand() % 6) + 1);
    }

    inline int getx() { return x; }
    inline int gety() { return y; }
    inline int getdirection() { return direction; }

    void move()
    {
        switch (direction)

        {
        case STOP:
            break;
        case lEFT:
            x--;
            break;
        case rIGHT:
            x++;
            break;
        case UPLEFT:
            x--;
            y--;
            break;
        case DOWNLEFT:
            x--;
            y++;
            break;
        case UPRIGHT:
            x++;
            y--;
            break;
        case DOWNRIGHT:
            x++;
            y++;
            break;
        default:
            break;
        }
    }

    friend ostream &operator<<(ostream &o, ball c)
    {
        o << "Ball[" << c.x << "," << c.y << "][" << c.direction << "]" << endl;
        return o;
    }
};

class racket
{
private:
    int x, y;
    int start_x, start_y;

public:
    racket()
    {
        x = y = 0;
    }
    racket(int posx, int posy) : racket()
    {
        start_x = posx;
        start_y = posy;
        x = posx;
        y = posy;
    }
    inline void reset()
    {
        x = start_x;
        y = start_y;
    }
    inline int getx() { return x; }
    inline int gety() { return y; }
    inline void moveup() { y--; }
    inline void movedown() { y++; }

    friend ostream &operator<<(ostream &o, racket c)
    {
        o << "racket[" << c.x << "," << c.y << "]";
        return o;
    }
};

class hand_cricket
{
private:
    int playerScore;
    int computerScore;

public:
    int Game()
    {
        playerScore = 0;
        computerScore = 0;
    }

    void play()
    {
        cout << "Welcome to Hand Cricket Game!" << endl;
        int toss = rand() % 2;
        if (toss == 0)
        {
            cout << "You won the toss!" << endl;
            playInnings(true);
            playInnings(false);
        }
        else
        {
            cout << "Computer won the toss!" << endl;
            playInnings(false);
            playInnings(true);
        }

        cout << "Game Over!" << endl;
        cout << "Your Score: " << playerScore << endl;
        cout << "Computer Score: " << computerScore << endl;
        if (playerScore > computerScore)
        {
            cout << "Congratulations! You won the game." << endl;
        }
        else if (playerScore < computerScore)
        {
            cout << "Sorry! You lost the game." << endl;
        }
        else
        {
            cout << "The game is tied." << endl;
        }
    }

    void playInnings(bool isPlayerBatting)
    {
        int score = 0;
        int computerNumber;
        int playerNumber;

        if (isPlayerBatting)
        {
            cout << "You are batting now!" << endl;
            do
            {
                cout << "Enter your number (1 to 6): ";
                cin >> playerNumber;
                computerNumber = rand() % 6 + 1;
                if (playerNumber < 1 || playerNumber > 6)
                {
                    cout << "Invalid number! Please enter a number between 1 and 6." << endl;
                }
                else
                {
                    cout << "Computer's number: " << computerNumber << endl;
                    if (playerNumber == computerNumber)
                    {
                        cout << "Out! Your innings is over." << endl;
                        break;
                    }
                    else
                    {
                        score += playerNumber;
                    }
                }
            } while (true);
        }
        else
        {
            cout << "Computer is batting now!" << endl;
            do
            {
                computerNumber = rand() % 6 + 1;
                cout << "Computer's number: " << computerNumber << endl;
                cout << "Enter your number (1 to 6): ";
                cin >> playerNumber;
                if (playerNumber < 1 || playerNumber > 6)
                {
                    cout << "Invalid number! Please enter a number between 1 and 6." << endl;
                }
                else
                {
                    if (playerNumber == computerNumber)
                    {
                        cout << "Out! Computer's innings is over." << endl;
                        break;
                    }
                    else
                    {
                        score += computerNumber;
                    }
                }
            } while (true);
        }
        if (isPlayerBatting)
        {
            playerScore = score;
            cout << "Your innings is over. Your score: " << playerScore << endl;
        }
        else
        {
            computerScore = score;
            cout << "Computer's innings is over. Computer's score: " << computerScore << endl;
        }
    }
};

class player
{
public:
    int x, y;
    player(int width)
    {
        x = width / 2;
        y = 0;
    }
};
class lane
{
private:
    deque<bool> cars;

public:
    lane(int width)
    {
        for (int i = 0; i < width; i++)
        {
            cars.push_front(true);
        }
    }
    void move()
    {
        if (rand() % 10 == 1)
            cars.push_front(true);
        else
            cars.push_front(false);
        cars.pop_back();
    }
    bool checkpos(int pos)
    {
        return cars[pos];
    }
};

class TicTacToe
{
public:
    char board[3][3];
    char currentPlayer;

    TicTacToe()
    {
        for (int i = 0; i < 3; i++)
        {
            for (int j = 0; j < 3; j++)
            {
                board[i][j] = '-';
            }
        }
        currentPlayer = 'X';
    }

    void printBoard()
    {
        cout << "   1 2 3" << endl;
        for (int i = 0; i < 3; i++)
        {
            cout << i + 1 << "  ";
            for (int j = 0; j < 3; j++)
            {
                cout << board[i][j] << " ";
            }
            cout << endl;
        }
    }

    bool play(int row, int col)
    {
        if (board[row - 1][col - 1] == '-')
        {
            board[row - 1][col - 1] = currentPlayer;
            if (currentPlayer == 'X')
            {
                currentPlayer = 'O';
            }
            else
            {
                currentPlayer = 'X';
            }
            return true;
        }
        else
        {
            return false;
        }
    }

    bool checkWin()
    {
        for (int i = 0; i < 3; i++)
        {
            if (board[i][0] == board[i][1] && board[i][1] == board[i][2] && board[i][0] != '-')
            {
                return true;
            }
            if (board[0][i] == board[1][i] && board[1][i] == board[2][i] && board[0][i] != '-')
            {
                return true;
            }
        }
        if (board[0][0] == board[1][1] && board[1][1] == board[2][2] && board[0][0] != '-')
        {
            return true;
        }
        if (board[0][2] == board[1][1] && board[1][1] == board[2][0] && board[0][2] != '-')
        {
            return true;
        }
        return false;
    }

    bool checkDraw()
    {
        for (int i = 0; i < 3; i++)
        {
            for (int j = 0; j < 3; j++)
            {
                if (board[i][j] == '-')
                {
                    return false;
                }
            }
        }
        return true;
    }
};

void Cdelay(int msec)
{
    long goal = msec + (clock());
    while (goal > (clock()))
        ;
}
void gotoXY(int X, int Y)
{
    COORD coordinates;
    coordinates.X = X;
    coordinates.Y = Y;
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), coordinates);
}
void loginFrame1(int xLenS = 18, int yLenS = 8, int xLenE = 55, int yLenE = 15)
{
    system("cls");
    gotoXY(xLenS, yLenS);
    printf("%c", 201);
    gotoXY(xLenS, yLenE);
    printf("%c", 200);

    for (int i = xLenS + 1; i <= xLenE - 1; i++) // Top and Bottom Border line
    {
        gotoXY(i, yLenS);
        printf("%c", 205);
        gotoXY(i, yLenE);
        printf("%c", 205);
    }
    gotoXY(xLenE, yLenS);
    printf("%c", 187);
    gotoXY(xLenE, yLenE);
    printf("%c", 188);
    for (int i = yLenS + 1; i <= yLenE - 1; i++) // Left and Right Border Line
    {
        gotoXY(xLenS, i);
        printf("%c", 186);
        gotoXY(xLenE, i);
        printf("%c", 186);
    }
    printf("\n\n");
}

void login()
{

    char UserName[30], Password[30], ch;
    int i = 0;
    gotoXY(20, 10);
    printf("Enter UserName : ");

    cin >> UserName;
    gotoXY(20, 12);
    cout << "Enter Password : ";
    while (1)
    {
        ch = getch();
        if (ch == 13)
            break;
        if (ch == 32 || ch == 9)
            continue;
        else
        {
            cout << "*";
            Password[i] = ch;
            i++;
        }
    }
    Password[i] = '\0';
    if (strcmp(UserName, "A4GAMING") == 0 && strcmp(Password, "A4") == 0)
    {
        system("cls");
        loginFrame1();
        gotoXY(27, 10);
        cout << "Login Success!!!";
        gotoXY(21, 12);
        cout << "Will be redirected in 3 Seconds...";
        gotoXY(56, 12);
        Cdelay(1000);
        gotoXY(44, 12);
        cout << "\b \b2";
        gotoXY(56, 12);
        Cdelay(1000);
        gotoXY(44, 12);
        cout << "\b \b1";
        gotoXY(56, 12);
        Cdelay(1000);
    }
    else
    {
        system("cls");
        loginFrame1();
        gotoXY(27, 10);
        printf("Access Denied!!!\a");
        gotoXY(21, 12);
        cout << "Will be redirected in 3 Seconds...";
        gotoXY(56, 12);
        Cdelay(1000);
        gotoXY(44, 12);
        cout << "\b \b2";
        gotoXY(56, 12);
        Cdelay(1000);
        gotoXY(44, 12);
        cout << "\b \b1";
        gotoXY(56, 12);
        Cdelay(1000);
        system("cls");
        loginFrame1();
        login();
    }
}

void borderNoDelay(int xLenS = 2, int yLenS = 2, int xLenE = 76, int yLenE = 24)
{
    system("cls");
    gotoXY(xLenS, yLenS);
    printf("%c", 201);

    gotoXY(xLenS, yLenE);
    printf("%c", 200);

    for (int i = xLenS + 1; i <= xLenE - 1; i++) // Top and Bottom Border line
    {
        gotoXY(i, yLenS);
        printf("%c", 205);
        gotoXY(i, yLenE);
        printf("%c", 205);
    }
    gotoXY(xLenE, yLenS);
    printf("%c", 187);
    gotoXY(xLenE, yLenE);
    printf("%c", 188);
    for (int i = yLenS + 1; i <= yLenE - 1; i++) // Left and Right Border Line
    {
        gotoXY(xLenS, i);
        printf("%c", 186);
        gotoXY(xLenE, i);
        printf("%c", 186);
    }
    printf("\n\n");
}
void intro()
{
    gotoXY(27, 4);
    printf("*/*  GAMING ARENA */*");
    gotoXY(24, 20);
    printf("Press Any key to continue...");
    getch();
}
int main()
{
    intro();
    system("cls");
    login();
    system("cls");
    while (1)
    {
        cout << "SELECT GAME YOU WANT TO PLAY";
        int choice;
    starting:
        cout << "WELCOME TO THE ARCADE.....\n";
        cout << "1.ROCK PAPER SCISSOR\n";
        cout << "2.FRUIT AND SNAKE\n";
        cout << "3.HAND CRICKET\n";
        cout << "4.CASINO NUMBER GUESSING\n";
        cout << "5.TIC TAC TOE\n";
        cout << "6.EXIT FROM CODE\n";
        cin >> choice;
        switch (choice)
        {
        case 1:
        {
            rps game; // Create a rock-paper-scissors game object
            game.play();
            Sleep(2500);
            break;
        }
        case 2:
        {
            fruit_and_snake game;
            game.play();
            Sleep(2500);
            break;
        }
        case 3:
        {
            hand_cricket game;
            game.play();
            Sleep(2500);
            break;
        }
        case 4:
        {
            casino();
            Sleep(2500);
            break;
        }
        case 5:
        {
            TicTacToe game;
            int row, col;
            bool win = false;
            bool draw = false;

            cout << "Tic Tac Toe" << endl;
            cout << "Player 1: X" << endl;
            cout << "Player 2: O" << endl;
            cout << endl;
            while (!win && !draw)
            {
                game.printBoard();

                int player = (game.currentPlayer == 'X') ? 1 : 2;
                cout << "Player " << player << ", enter row and column (1-3): ";
                cin >> row >> col;

                if (game.play(row, col))
                {
                    win = game.checkWin();
                    draw = game.checkDraw();
                }
                else
                {
                    cout << "Invalid move. Try again." << endl;
                }
            }
            game.printBoard();
            if (win)
            {
                int player = (game.currentPlayer == 'X') ? 2 : 1;
                cout << "Player" << player << " wins!" << endl;
            }
            else
            {
                cout << "It's a draw!" << endl;
            }
        }
            Sleep(2500);
            break;
        case 6:
        {
            exit(0);
        }
        default:
        {
            goto starting;
        }
        }
        system("cls");
    }
    return 0;
}
