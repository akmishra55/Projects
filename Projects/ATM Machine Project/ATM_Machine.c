#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <conio.h> // For getch() on Windows

#ifdef _WIN32
    #include <windows.h>
    #define CLEAR_SCREEN system("cls")
    #define strcasecmp _stricmp
#else
    #include <unistd.h>
    #define CLEAR_SCREEN system("clear")
    #define strcasecmp strcasecmp
#endif

// Global variables
int main_exit;
const char ADMIN_PASSWORD[] = "admin123"; // Changed password for security

// Structure definitions
struct Date {
    int month, day, year;
};

struct Account {
    int acc_no;
    char name[60];
    struct Date dob;
    int age;
    char address[100];
    char citizenship[20];
    char phone[15];
    char acc_type[15];
    float balance;
    struct Date deposit_date;
    struct Date last_transaction;
};

// Function prototypes
void menu(void);
void newAccount(void);
void viewList(void);
void editAccount(void);
void transact(void);
void eraseAccount(void);
void viewAccount(void);
void closeProgram(void);
void delay(int milliseconds);
void printHeader(const char* title);
int validateDate(struct Date d);
int isAccountExists(int acc_no);
void saveAccount(struct Account acc);
void displayAccount(struct Account acc);
float calculateInterest(struct Account acc);

// Utility functions
void delay(int milliseconds) {
    #ifdef _WIN32
        Sleep(milliseconds);
    #else
        usleep(milliseconds * 1000);
    #endif
}

void printHeader(const char* title) {
    CLEAR_SCREEN;
    printf("\n");
    for(int i = 0; i < 60; i++) printf("=");
    printf("\n\t\t%s\n", title);
    for(int i = 0; i < 60; i++) printf("=");
    printf("\n\n");
}

int validateDate(struct Date d) {
    if (d.year < 1900 || d.year > 2100) return 0;
    if (d.month < 1 || d.month > 12) return 0;
    
    int daysInMonth[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    
    // Check for leap year
    if ((d.year % 4 == 0 && d.year % 100 != 0) || (d.year % 400 == 0)) {
        daysInMonth[1] = 29;
    }
    
    if (d.day < 1 || d.day > daysInMonth[d.month - 1]) return 0;
    
    return 1;
}

int isAccountExists(int acc_no) {
    FILE *fp = fopen("record.dat", "r");
    if (fp == NULL) return 0;
    
    struct Account temp;
    while(fread(&temp, sizeof(struct Account), 1, fp)) {
        if (temp.acc_no == acc_no) {
            fclose(fp);
            return 1;
        }
    }
    fclose(fp);
    return 0;
}

void saveAccount(struct Account acc) {
    FILE *fp = fopen("record.dat", "ab");
    if (fp != NULL) {
        fwrite(&acc, sizeof(struct Account), 1, fp);
        fclose(fp);
    }
}

float calculateInterest(struct Account acc) {
    if (strcasecmp(acc.acc_type, "fixed1") == 0) {
        return (acc.balance * 9 * 1) / 100.0;
    } else if (strcasecmp(acc.acc_type, "fixed2") == 0) {
        return (acc.balance * 11 * 2) / 100.0;
    } else if (strcasecmp(acc.acc_type, "fixed3") == 0) {
        return (acc.balance * 13 * 3) / 100.0;
    } else if (strcasecmp(acc.acc_type, "saving") == 0) {
        return (acc.balance * 8) / (100.0 * 12.0); // Monthly interest
    }
    return 0.0;
}

void displayAccount(struct Account acc) {
    printf("\n═══════════════════════════════════════════════════════\n");
    printf("Account No.    : %d\n", acc.acc_no);
    printf("Name           : %s\n", acc.name);
    printf("Date of Birth  : %02d/%02d/%04d\n", acc.dob.month, acc.dob.day, acc.dob.year);
    printf("Age            : %d\n", acc.age);
    printf("Address        : %s\n", acc.address);
    printf("Citizenship    : %s\n", acc.citizenship);
    printf("Phone          : %s\n", acc.phone);
    printf("Account Type   : %s\n", acc.acc_type);
    printf("Balance        : $%.2f\n", acc.balance);
    printf("Date Opened    : %02d/%02d/%04d\n", 
           acc.deposit_date.month, acc.deposit_date.day, acc.deposit_date.year);
    
    float interest = calculateInterest(acc);
    if (interest > 0) {
        printf("Expected Interest: $%.2f\n", interest);
    }
    printf("═══════════════════════════════════════════════════════\n");
}

// Main functions
void newAccount(void) {
    struct Account new_acc;
    char choice;
    
    do {
        printHeader("CREATE NEW ACCOUNT");
        
        // Get account number
        do {
            printf("Enter Account Number (6 digits): ");
            scanf("%d", &new_acc.acc_no);
            if (new_acc.acc_no < 100000 || new_acc.acc_no > 999999) {
                printf("Account number must be 6 digits!\n");
            } else if (isAccountExists(new_acc.acc_no)) {
                printf("Account number already exists!\n");
                new_acc.acc_no = -1;
            }
        } while(new_acc.acc_no < 100000 || new_acc.acc_no > 999999);
        
        // Get account details
        printf("Enter Name: ");
        scanf(" %[^\n]s", new_acc.name);
        
        // Get date of birth
        do {
            printf("Enter Date of Birth (MM/DD/YYYY): ");
            scanf("%d/%d/%d", &new_acc.dob.month, &new_acc.dob.day, &new_acc.dob.year);
            if (!validateDate(new_acc.dob)) {
                printf("Invalid date! Please try again.\n");
            }
        } while(!validateDate(new_acc.dob));
        
        // Calculate age
        printf("Enter Age: ");
        scanf("%d", &new_acc.age);
        
        printf("Enter Address: ");
        scanf(" %[^\n]s", new_acc.address);
        
        printf("Enter Citizenship: ");
        scanf(" %[^\n]s", new_acc.citizenship);
        
        printf("Enter Phone Number: ");
        scanf(" %[^\n]s", new_acc.phone);
        
        // Get account type
        printf("\nAccount Types:\n");
        printf("1. Savings (8%% annual interest)\n");
        printf("2. Current (No interest)\n");
        printf("3. Fixed Deposit - 1 year (9%% interest)\n");
        printf("4. Fixed Deposit - 2 years (11%% interest)\n");
        printf("5. Fixed Deposit - 3 years (13%% interest)\n");
        
        int type_choice;
        do {
            printf("Choose account type (1-5): ");
            scanf("%d", &type_choice);
        } while(type_choice < 1 || type_choice > 5);
        
        switch(type_choice) {
            case 1: strcpy(new_acc.acc_type, "saving"); break;
            case 2: strcpy(new_acc.acc_type, "current"); break;
            case 3: strcpy(new_acc.acc_type, "fixed1"); break;
            case 4: strcpy(new_acc.acc_type, "fixed2"); break;
            case 5: strcpy(new_acc.acc_type, "fixed3"); break;
        }
        
        // Get initial deposit
        do {
            printf("Enter Initial Deposit ($): ");
            scanf("%f", &new_acc.balance);
            if (new_acc.balance < 0) {
                printf("Amount cannot be negative!\n");
            }
        } while(new_acc.balance < 0);
        
        // Get current date
        printf("Enter Today's Date (MM/DD/YYYY): ");
        scanf("%d/%d/%d", &new_acc.deposit_date.month, 
                         &new_acc.deposit_date.day, 
                         &new_acc.deposit_date.year);
        
        new_acc.last_transaction = new_acc.deposit_date;
        
        // Save account
        saveAccount(new_acc);
        printf("\n✓ Account created successfully!\n");
        
        printf("\nCreate another account? (Y/N): ");
        scanf(" %c", &choice);
    } while(toupper(choice) == 'Y');
    
    menu();
}

void viewList(void) {
    printHeader("VIEW ALL ACCOUNTS");
    
    FILE *fp = fopen("record.dat", "rb");
    if (fp == NULL) {
        printf("No accounts found!\n");
        printf("\nPress any key to continue...");
        getch();
        menu();
        return;
    }
    
    printf("%-10s %-25s %-15s %-12s\n", 
           "Acc No.", "Name", "Phone", "Balance");
    printf("═══════════════════════════════════════════════════════════\n");
    
    struct Account acc;
    int count = 0;
    
    while(fread(&acc, sizeof(struct Account), 1, fp)) {
        printf("%-10d %-25s %-15s $%-10.2f\n", 
               acc.acc_no, acc.name, acc.phone, acc.balance);
        count++;
    }
    
    fclose(fp);
    
    printf("\n═══════════════════════════════════════════════════════════\n");
    printf("Total Accounts: %d\n", count);
    
    printf("\nPress any key to continue...");
    getch();
    menu();
}

void editAccount(void) {
    printHeader("EDIT ACCOUNT INFORMATION");
    
    int acc_no;
    printf("Enter Account Number to edit: ");
    scanf("%d", &acc_no);
    
    if (!isAccountExists(acc_no)) {
        printf("Account not found!\n");
        printf("\nPress any key to continue...");
        getch();
        menu();
        return;
    }
    
    FILE *fp = fopen("record.dat", "rb");
    FILE *temp = fopen("temp.dat", "wb");
    
    struct Account acc;
    int found = 0;
    
    while(fread(&acc, sizeof(struct Account), 1, fp)) {
        if (acc.acc_no == acc_no) {
            found = 1;
            displayAccount(acc);
            
            int choice;
            printf("\nWhat would you like to edit?\n");
            printf("1. Address\n");
            printf("2. Phone Number\n");
            printf("Enter choice: ");
            scanf("%d", &choice);
            
            if (choice == 1) {
                printf("Enter new address: ");
                scanf(" %[^\n]s", acc.address);
                printf("✓ Address updated successfully!\n");
            } else if (choice == 2) {
                printf("Enter new phone number: ");
                scanf(" %[^\n]s", acc.phone);
                printf("✓ Phone number updated successfully!\n");
            } else {
                printf("Invalid choice!\n");
            }
        }
        fwrite(&acc, sizeof(struct Account), 1, temp);
    }
    
    fclose(fp);
    fclose(temp);
    
    remove("record.dat");
    rename("temp.dat", "record.dat");
    
    printf("\nPress any key to continue...");
    getch();
    menu();
}

void transact(void) {
    printHeader("ACCOUNT TRANSACTION");
    
    int acc_no;
    printf("Enter Account Number: ");
    scanf("%d", &acc_no);
    
    if (!isAccountExists(acc_no)) {
        printf("Account not found!\n");
        printf("\nPress any key to continue...");
        getch();
        menu();
        return;
    }
    
    FILE *fp = fopen("record.dat", "rb");
    FILE *temp = fopen("temp.dat", "wb");
    
    struct Account acc;
    int found = 0;
    
    while(fread(&acc, sizeof(struct Account), 1, fp)) {
        if (acc.acc_no == acc_no) {
            found = 1;
            displayAccount(acc);
            
            // Check if fixed deposit account
            if (strstr(acc.acc_type, "fixed") != NULL) {
                printf("\n⚠ Fixed deposit accounts cannot have transactions!\n");
                fwrite(&acc, sizeof(struct Account), 1, temp);
                continue;
            }
            
            int choice;
            printf("\nTransaction Type:\n");
            printf("1. Deposit\n");
            printf("2. Withdraw\n");
            printf("Enter choice: ");
            scanf("%d", &choice);
            
            float amount;
            if (choice == 1) {
                printf("Enter deposit amount ($): ");
                scanf("%f", &amount);
                if (amount > 0) {
                    acc.balance += amount;
                    printf("✓ $%.2f deposited successfully!\n", amount);
                    printf("✓ New Balance: $%.2f\n", acc.balance);
                } else {
                    printf("Invalid amount!\n");
                }
            } else if (choice == 2) {
                printf("Enter withdrawal amount ($): ");
                scanf("%f", &amount);
                if (amount > 0 && amount <= acc.balance) {
                    acc.balance -= amount;
                    printf("✓ $%.2f withdrawn successfully!\n", amount);
                    printf("✓ New Balance: $%.2f\n", acc.balance);
                } else if (amount > acc.balance) {
                    printf("⚠ Insufficient balance!\n");
                } else {
                    printf("Invalid amount!\n");
                }
            }
        }
        fwrite(&acc, sizeof(struct Account), 1, temp);
    }
    
    fclose(fp);
    fclose(temp);
    
    remove("record.dat");
    rename("temp.dat", "record.dat");
    
    printf("\nPress any key to continue...");
    getch();
    menu();
}

void eraseAccount(void) {
    printHeader("DELETE ACCOUNT");
    
    int acc_no;
    printf("Enter Account Number to delete: ");
    scanf("%d", &acc_no);
    
    if (!isAccountExists(acc_no)) {
        printf("Account not found!\n");
        printf("\nPress any key to continue...");
        getch();
        menu();
        return;
    }
    
    char confirm;
    printf("Are you sure you want to delete account %d? (Y/N): ", acc_no);
    scanf(" %c", &confirm);
    
    if (toupper(confirm) != 'Y') {
        printf("Deletion cancelled.\n");
        printf("\nPress any key to continue...");
        getch();
        menu();
        return;
    }
    
    FILE *fp = fopen("record.dat", "rb");
    FILE *temp = fopen("temp.dat", "wb");
    
    struct Account acc;
    int deleted = 0;
    
    while(fread(&acc, sizeof(struct Account), 1, fp)) {
        if (acc.acc_no != acc_no) {
            fwrite(&acc, sizeof(struct Account), 1, temp);
        } else {
            deleted = 1;
        }
    }
    
    fclose(fp);
    fclose(temp);
    
    remove("record.dat");
    rename("temp.dat", "record.dat");
    
    if (deleted) {
        printf("✓ Account deleted successfully!\n");
    }
    
    printf("\nPress any key to continue...");
    getch();
    menu();
}

void viewAccount(void) {
    printHeader("VIEW ACCOUNT DETAILS");
    
    int choice;
    printf("Search by:\n");
    printf("1. Account Number\n");
    printf("2. Name\n");
    printf("Enter choice: ");
    scanf("%d", &choice);
    
    FILE *fp = fopen("record.dat", "rb");
    if (fp == NULL) {
        printf("No accounts found!\n");
        printf("\nPress any key to continue...");
        getch();
        menu();
        return;
    }
    
    struct Account acc;
    int found = 0;
    
    if (choice == 1) {
        int acc_no;
        printf("Enter Account Number: ");
        scanf("%d", &acc_no);
        
        while(fread(&acc, sizeof(struct Account), 1, fp)) {
            if (acc.acc_no == acc_no) {
                displayAccount(acc);
                found = 1;
                break;
            }
        }
    } else if (choice == 2) {
        char name[60];
        printf("Enter Name: ");
        scanf(" %[^\n]s", name);
        
        while(fread(&acc, sizeof(struct Account), 1, fp)) {
            if (strcasecmp(acc.name, name) == 0) {
                displayAccount(acc);
                found = 1;
                break;
            }
        }
    }
    
    fclose(fp);
    
    if (!found) {
        printf("Account not found!\n");
    }
    
    printf("\nPress any key to continue...");
    getch();
    menu();
}

void closeProgram(void) {
    printHeader("ATM MANAGEMENT SYSTEM");
    printf("\n\n\tThank you for using our banking system!\n");
    printf("\tDeveloped by: Student Team\n");
    printf("\tVersion: 2.0\n\n");
    exit(0);
}

void menu(void) {
    int choice;
    
    printHeader("ATM MANAGEMENT SYSTEM");
    printf("\t\tMAIN MENU\n\n");
    
    printf("1. Create New Account\n");
    printf("2. Update Account Information\n");
    printf("3. Perform Transaction\n");
    printf("4. View Account Details\n");
    printf("5. Delete Account\n");
    printf("6. View All Accounts\n");
    printf("7. Exit\n\n");
    
    printf("Enter your choice (1-7): ");
    scanf("%d", &choice);
    
    switch(choice) {
        case 1: newAccount(); break;
        case 2: editAccount(); break;
        case 3: transact(); break;
        case 4: viewAccount(); break;
        case 5: eraseAccount(); break;
        case 6: viewList(); break;
        case 7: closeProgram(); break;
        default:
            printf("Invalid choice! Please try again.\n");
            delay(1000);
            menu();
    }
}

int main() {
    char password[20];
    int attempts = 3;
    
    #ifdef _WIN32
        system("color 0A"); // Green text on black background
    #endif
    
    while(attempts > 0) {
        printHeader("ATM MANAGEMENT SYSTEM - LOGIN");
        
        printf("Enter Password: ");
        
        // Simple password masking
        int i = 0;
        while(1) {
            char ch = getch();
            if (ch == 13) { // Enter key
                password[i] = '\0';
                break;
            } else if (ch == 8) { // Backspace
                if (i > 0) {
                    i--;
                    printf("\b \b");
                }
            } else {
                if (i < 19) {
                    password[i] = ch;
                    i++;
                    printf("*");
                }
            }
        }
        
        if (strcmp(password, ADMIN_PASSWORD) == 0) {
            printf("\n\n✓ Login successful! Loading");
            for(int i = 0; i < 3; i++) {
                printf(".");
                delay(500);
            }
            menu();
            break;
        } else {
            attempts--;
            if (attempts > 0) {
                printf("\n\n✗ Wrong password! %d attempts remaining.\n", attempts);
                delay(2000);
            } else {
                printf("\n\n✗ Access denied! Too many failed attempts.\n");
                delay(2000);
                exit(1);
            }
        }
    }
    
    return 0;
}