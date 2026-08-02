#include "basefile.hpp"
#include <cmath>

class Matrix {
private:
    int M;
    int N;
    float** values;
    
public:
    Matrix(int n);
    Matrix(int m, int n, float fill_value = 0.0f);
    Matrix(const Matrix& other);
    Matrix(Matrix&& other);

    Matrix& operator=(const Matrix& other);
    Matrix& operator=(Matrix&& other);
    
    Matrix& operator*=(float inc);
    Matrix& operator+=(const Matrix& other);
    Matrix& operator-=(const Matrix& other);
    Matrix& operator/=(float inc);
    
    Matrix operator+(const Matrix& other) const;
    Matrix operator-(const Matrix& other) const;
    Matrix operator*(const Matrix& other) const;
    Matrix operator*(float inc) const;
    Matrix operator/(float inc) const;

    ~Matrix();

    float get(int i, int j) const;
    const float* get_row(int row_index) const;
    void set(int i, int j, float value);
    int get_width() const;
    int get_height() const;
    void negate();
    void add_in_place(const Matrix& other);
    Matrix multiply(const Matrix& other);
    
    bool load_from_file(const char* filename);
};

// Глобальные операторы
Matrix operator*(float inc, const Matrix& m);
Matrix operator-(const Matrix& m);