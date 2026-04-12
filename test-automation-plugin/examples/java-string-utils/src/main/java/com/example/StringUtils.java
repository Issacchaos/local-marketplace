package com.example;

/**
 * A utility class for common string operations.
 *
 * This class provides various string manipulation methods including
 * capitalization, reversal, palindrome checking, and more.
 *
 * @author Claude Code Testing Plugin Example
 * @version 1.0
 */
public class StringUtils {

    /**
     * Capitalizes the first letter of a string.
     *
     * @param input the string to capitalize
     * @return the capitalized string, or null if input is null
     * @throws IllegalArgumentException if the string is empty
     */
    public static String capitalize(String input) {
        if (input == null) {
            return null;
        }
        if (input.isEmpty()) {
            throw new IllegalArgumentException("Cannot capitalize an empty string");
        }
        return input.substring(0, 1).toUpperCase() + input.substring(1);
    }

    /**
     * Reverses a string.
     *
     * @param input the string to reverse
     * @return the reversed string, or null if input is null
     */
    public static String reverse(String input) {
        if (input == null) {
            return null;
        }
        return new StringBuilder(input).reverse().toString();
    }

    /**
     * Checks if a string is a palindrome (reads the same forwards and backwards).
     * Case-insensitive comparison.
     *
     * @param input the string to check
     * @return true if the string is a palindrome, false otherwise
     * @throws IllegalArgumentException if the input is null
     */
    public static boolean isPalindrome(String input) {
        if (input == null) {
            throw new IllegalArgumentException("Input cannot be null");
        }
        String normalized = input.toLowerCase();
        return normalized.equals(new StringBuilder(normalized).reverse().toString());
    }

    /**
     * Counts the number of vowels in a string.
     *
     * @param input the string to analyze
     * @return the number of vowels (a, e, i, o, u), case-insensitive
     */
    public static int countVowels(String input) {
        if (input == null || input.isEmpty()) {
            return 0;
        }
        int count = 0;
        String vowels = "aeiouAEIOU";
        for (char c : input.toCharArray()) {
            if (vowels.indexOf(c) != -1) {
                count++;
            }
        }
        return count;
    }

    /**
     * Repeats a string a specified number of times.
     *
     * @param input the string to repeat
     * @param times the number of times to repeat
     * @return the repeated string
     * @throws IllegalArgumentException if times is negative
     */
    public static String repeat(String input, int times) {
        if (times < 0) {
            throw new IllegalArgumentException("Repeat count cannot be negative");
        }
        if (input == null) {
            return null;
        }
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < times; i++) {
            result.append(input);
        }
        return result.toString();
    }

    /**
     * Truncates a string to a maximum length, adding an ellipsis if truncated.
     *
     * @param input the string to truncate
     * @param maxLength the maximum length (including ellipsis)
     * @return the truncated string with "..." appended if truncated
     * @throws IllegalArgumentException if maxLength is less than 3
     */
    public static String truncate(String input, int maxLength) {
        if (maxLength < 3) {
            throw new IllegalArgumentException("Max length must be at least 3 to accommodate ellipsis");
        }
        if (input == null) {
            return null;
        }
        if (input.length() <= maxLength) {
            return input;
        }
        return input.substring(0, maxLength - 3) + "...";
    }

    /**
     * Checks if a string contains only alphabetic characters.
     *
     * @param input the string to check
     * @return true if the string contains only letters, false otherwise
     */
    public static boolean isAlphabetic(String input) {
        if (input == null || input.isEmpty()) {
            return false;
        }
        for (char c : input.toCharArray()) {
            if (!Character.isLetter(c)) {
                return false;
            }
        }
        return true;
    }

    /**
     * Removes all whitespace from a string.
     *
     * @param input the string to process
     * @return the string with all whitespace removed
     */
    public static String removeWhitespace(String input) {
        if (input == null) {
            return null;
        }
        return input.replaceAll("\\s+", "");
    }

    /**
     * Counts the number of words in a string.
     * Words are separated by whitespace.
     *
     * @param input the string to analyze
     * @return the number of words
     */
    public static int countWords(String input) {
        if (input == null || input.trim().isEmpty()) {
            return 0;
        }
        String[] words = input.trim().split("\\s+");
        return words.length;
    }

    /**
     * Converts a string to title case (first letter of each word capitalized).
     *
     * @param input the string to convert
     * @return the title case string
     */
    public static String toTitleCase(String input) {
        if (input == null || input.isEmpty()) {
            return input;
        }
        String[] words = input.split("\\s+");
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < words.length; i++) {
            if (!words[i].isEmpty()) {
                result.append(Character.toUpperCase(words[i].charAt(0)))
                      .append(words[i].substring(1).toLowerCase());
                if (i < words.length - 1) {
                    result.append(" ");
                }
            }
        }
        return result.toString();
    }
}
