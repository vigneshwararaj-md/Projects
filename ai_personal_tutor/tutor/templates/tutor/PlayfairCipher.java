import java.util.Scanner;

public class PlayfairCipher {
    private char[][] keyTable = new char[5][5];

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        PlayfairCipher cipher = new PlayfairCipher();

        System.out.println("=== PLAYFAIR CIPHER ===");

        // Step 1: Generate the 5x5 key table with user-specified order
        cipher.generateKeyTableAlt(scanner);

        // Display key table
        System.out.println("\nKey Table (5x5):");
        cipher.displayKeyTable();

        // Get plaintext
        System.out.print("\nEnter the plaintext to encrypt: ");
        String plaintext = scanner.nextLine().toUpperCase();

        // Encrypt
        String ciphertext = cipher.encrypt(plaintext);
        System.out.println("\nEncrypted Text: " + ciphertext);

        // Decrypt
        String decryptedText = cipher.decrypt(ciphertext);
        System.out.println("Decrypted Text: " + decryptedText);

        scanner.close();
    }

    // Step 1: Generate the 5x5 key table with user-specified order


    // Alternative method: User can enter all 25 letters at once
    public void generateKeyTableAlt(Scanner scanner) {
        System.out.println("\nEnter all 25 letters in order (row by row):");
        System.out.println("Example: MONARCHYBDEFGIKLPSTUVWXZ");
        System.out.print("Enter: ");

        String allLetters = scanner.nextLine().toUpperCase();
        allLetters = allLetters.replaceAll("[^A-Z]", "");

        if (allLetters.length() != 25) {
            System.out.println("Error: Need exactly 25 letters!");
            System.out.println("You entered " + allLetters.length() + " letters.");
            return;
        }

        boolean[] used = new boolean[26];
        int index = 0;

        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                char ch = allLetters.charAt(index);

                if (ch == 'J') ch = 'I';

                if (ch == 'Q') {
                    System.out.println("Error: 'Q' should be omitted!");
                    return;
                }

                if (used[ch - 'A']) {
                    System.out.println("Error: Duplicate letter '" + ch + "'!");
                    return;
                }

                keyTable[i][j] = ch;
                used[ch - 'A'] = true;
                index++;
            }
        }

        // Check if all letters (except Q and J) are used
        int count = 0;
        for (int i = 0; i < 26; i++) {
            if (i != ('Q' - 'A') && i != ('J' - 'A') && used[i]) {
                count++;
            }
        }

        if (count != 25) {
            System.out.println("Error: Must use all letters except Q (and J is replaced by I)!");
        }
    }

    // Display the key table
    public void displayKeyTable() {
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                System.out.print(keyTable[i][j] + " ");
            }
            System.out.println();
        }
    }

    // Step 2 & 3 & 4: Prepare plaintext for encryption
    public String prepareText(String text) {
        StringBuilder prepared = new StringBuilder();

        // Step 2: Remove punctuation and keep only letters
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (ch >= 'A' && ch <= 'Z') {
                if (ch == 'J') ch = 'I'; // Replace J with I
                prepared.append(ch);
            }
        }

        // Step 3: Insert 'X' between double letters
        StringBuilder withX = new StringBuilder();
        for (int i = 0; i < prepared.length(); i++) {
            withX.append(prepared.charAt(i));
            if (i < prepared.length() - 1 && prepared.charAt(i) == prepared.charAt(i + 1)) {
                withX.append('X');
            }
        }

        // Step 4: Ensure even length (add X if odd)
        if (withX.length() % 2 != 0) {
            withX.append('X');
        }

        return withX.toString();
    }

    // Find position of a letter in key table
    public int[] findPosition(char ch) {
        int[] pos = new int[2];
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                if (keyTable[i][j] == ch) {
                    pos[0] = i;
                    pos[1] = j;
                    return pos;
                }
            }
        }
        return pos;
    }

    // Step 5: Encryption
    public String encrypt(String plaintext) {
        String prepared = prepareText(plaintext);
        StringBuilder ciphertext = new StringBuilder();

        // Split into digraphs
        for (int i = 0; i < prepared.length(); i += 2) {
            char first = prepared.charAt(i);
            char second = prepared.charAt(i + 1);

            int[] pos1 = findPosition(first);
            int[] pos2 = findPosition(second);

            // Step 5a: Same row
            if (pos1[0] == pos2[0]) {
                int col1 = (pos1[1] + 1) % 5;
                int col2 = (pos2[1] + 1) % 5;
                ciphertext.append(keyTable[pos1[0]][col1]);
                ciphertext.append(keyTable[pos2[0]][col2]);
            }
            // Step 5b: Same column
            else if (pos1[1] == pos2[1]) {
                int row1 = (pos1[0] + 1) % 5;
                int row2 = (pos2[0] + 1) % 5;
                ciphertext.append(keyTable[row1][pos1[1]]);
                ciphertext.append(keyTable[row2][pos2[1]]);
            }
            // Step 5c: Different rows and columns
            else {
                ciphertext.append(keyTable[pos1[0]][pos2[1]]);
                ciphertext.append(keyTable[pos2[0]][pos1[1]]);
            }
        }

        return ciphertext.toString();
    }

    // Step 6: Decryption
    public String decrypt(String ciphertext) {
        StringBuilder plaintext = new StringBuilder();

        // Split into digraphs
        for (int i = 0; i < ciphertext.length(); i += 2) {
            char first = ciphertext.charAt(i);
            char second = ciphertext.charAt(i + 1);

            int[] pos1 = findPosition(first);
            int[] pos2 = findPosition(second);

            // Step 6a: Same row - shift left
            if (pos1[0] == pos2[0]) {
                int col1 = (pos1[1] - 1 + 5) % 5;
                int col2 = (pos2[1] - 1 + 5) % 5;
                plaintext.append(keyTable[pos1[0]][col1]);
                plaintext.append(keyTable[pos2[0]][col2]);
            }
            // Step 6b: Same column - shift up
            else if (pos1[1] == pos2[1]) {
                int row1 = (pos1[0] - 1 + 5) % 5;
                int row2 = (pos2[0] - 1 + 5) % 5;
                plaintext.append(keyTable[row1][pos1[1]]);
                plaintext.append(keyTable[row2][pos2[1]]);
            }
            // Step 6c: Different rows and columns
            else {
                plaintext.append(keyTable[pos1[0]][pos2[1]]);
                plaintext.append(keyTable[pos2[0]][pos1[1]]);
            }
        }

        return plaintext.toString();
    }
}